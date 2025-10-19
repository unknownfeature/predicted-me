import datetime
import json
import os
import traceback
import uuid
from enum import Enum
from typing import Dict, Any, List, Set, Callable, Tuple, Optional

import boto3
from croniter import croniter
from sqlalchemy import select, and_, Executable
from sqlalchemy.orm import Session

from shared import constants
from backend.lib.db import User, Tag, Metric, normalize_identifier, Task, get_utc_timestamp
from shared.variables import aws_region, gemini_api_key


class HttpMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'


def get_or_create_task(session: Session, display_summary: str, description: str, user_id: int, id: int = None) -> Task:
    summary = normalize_identifier(display_summary)
    conditions = [Task.user_id == user_id, Task.summary == summary]
    if id:
        conditions.append(Task.id == id)
    existing = session.scalars(
        select(Task).where(and_(*conditions))).first()

    if not existing:
        new_one = Task(user_id=user_id, summary=summary, display_summary=display_summary, description=description)
        session.add(new_one)
        session.flush()
        return new_one
    return existing


def get_or_create_tasks(session: Session, names_to_display_names: Dict[str, Dict[str, str]], user_id: int) -> Dict[
    str, Task]:
    existing = {m.summary: m for m in
                session.scalars(select(Task).where(
                    and_(Task.user_id == user_id, Task.summary.in_(names_to_display_names.keys())))).unique()}
    non_existing = set(names_to_display_names.keys()).difference(existing.keys())

    results = {
        name: Task(summary=name, user_id=user_id, display_summary=names_to_display_names[name][constants.summary],
                   description=names_to_display_names[name][constants.description]) for name in
        non_existing}

    if results:
        session.add_all(results.values())
        return results | existing

    return existing


def get_or_create_metrics(session: Session, summary_to_display_summary: Dict[str, str], user_id: int) -> Dict[
    str, Metric]:
    existing = {m.name: m for m in
                session.scalars(select(Metric).where(
                    and_(Metric.user_id == user_id, Metric.name.in_(summary_to_display_summary.keys())))).unique()}
    non_existing = set(summary_to_display_summary.keys()).difference(existing.keys())

    results = {name: Metric(name=name, user_id=user_id, display_name=summary_to_display_summary[name]) for name in
               non_existing}

    if results:
        session.add_all(results.values())
        return results | existing

    return existing


def get_user_ids_from_event(event: Dict[str, Any], session: Session) -> Tuple[int, str]:
    external_user = event['requestContext']['authorizer']['jwt']['claims']['cognito:username']
    user_query = select(User.id).where(User.external_id == external_user)
    user = session.execute(user_query).first()

    return user.id if user else None, external_user

def call_generative(model: str, prompt: str, text_content: str, max_tokens: int = 3072) -> List[Dict[str, Any]]:
    try:
        bedrock_runtime = boto3.client(constants.bedrock_runtime)

        id = uuid.uuid4().hex
        response = bedrock_runtime.invoke_model(
            modelId=model,
            accept=constants.application_json,
            contentType=constants.application_json,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': max_tokens,
                'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': (prompt if prompt else '') + (
                    f'TEXT FOR ANALYSIS:    ---START_USER_INPUT {id} ---  {text_content} ---END_USER_INPUT  {id} ---'
                ) if text_content else ''}]}],
            })
        )

        response_body = json.loads(response[constants.body].read())
        metrics_json_str = response_body[constants.content][0][constants.text].strip()

        if metrics_json_str.startswith('```'):
            metrics_json_str = metrics_json_str.split('\n', 1)[-1].strip('`')

        return json.loads(metrics_json_str)

    except Exception as e:
        traceback.print_exc()
        raise e


def call_embedding(model: str, text_content: str) -> Optional[List[float]]:
    try:
        bedrock_runtime = boto3.client(constants.bedrock_runtime)

        body = json.dumps({constants.input_text: text_content})
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model,
            accept=constants.application_json,
            contentType=constants.application_json
        )
        response_body = json.loads(response.get(constants.body).read())
        return response_body.get(constants.embedding)

    except Exception as e:
        traceback.print_exc()
        raise e



def cron_expression_from_dict(data: Dict[str, str]) -> str:
    return f'0 {data[constants.minute]} {data[constants.hour]} {data[constants.day_of_month]} {data[constants.month]} {data[constants.day_of_week]}'


def cron_expression_from_schedule(schedule: Any) -> str:
    return f'0 {schedule.minute} {schedule.hour} {schedule.day_of_month} {schedule.month} {schedule.day_of_week}'


def enrich_schedule_map_with_next_timestamp(data_from_the_client: Dict[str, str]) -> Dict[str, str]:
    #  if no keys it will fail and that's what it should do
    next_run = get_next_run_timestamp(cron_expression_from_dict(data_from_the_client), period_seconds=data_from_the_client.get(constants.period_seconds))
    data_from_the_client[constants.next_run] = next_run
    return data_from_the_client


def get_next_run_timestamp(cron_expression: str, base_time: int = None, period_seconds: int =None) -> int:
    if not base_time:
        base_time = get_utc_timestamp()

    if period_seconds is not None and period_seconds > 0:
        return base_time + period_seconds

    iterator = croniter(cron_expression, datetime.datetime.fromtimestamp(base_time, datetime.timezone.utc))
    next_run_datetime = iterator.get_next(datetime.datetime)
    return int(next_run_datetime.timestamp())


def get_or_create_tags(user_id: int, session: Session, tag_display_names: Set[str]) -> Dict[str, Tag]:
    if not tag_display_names:
        return {}

    names_map = {normalize_identifier(name): name for name in tag_display_names}
    stmt = select(Tag).where(and_(Tag.name.in_(names_map.keys()), Tag.user_id == user_id))
    existing_tags = session.scalars(stmt).all()
    existing_tags_dict = {tag.name: tag for tag in existing_tags}
    new_tags = {t: Tag(user_id=user_id, name=t, display_name=names_map[t]) for t in names_map if
                t not in existing_tags_dict}

    if new_tags:
        session.add_all(new_tags.values())
        session.flush()

    return existing_tags_dict | new_tags


# todo refactor this
def add_tags(user_id: int, session: Session, data: List[Dict[str, Any]], stmt_supplier: Callable[[], Executable]):
    if not data:
        return

    tag_map = get_tags_map_for_update(user_id, data, session)
    data_map = {item[constants.id]: [normalize_identifier(t) for t in item.get(constants.tags, [])] for item in data}

    entities_to_update = session.scalars(stmt_supplier()).unique().all()
    for entity in entities_to_update:
        entity.tags.clear()
        entity.tags.extend([tag_map[tag_name] for tag_name in data_map[entity.id] if
                            tag_name not in {tag.name for tag in entity.tags}])
        entity.tagged = True


def get_tags_map_for_update(user_id: int, data: List[Dict[str, str]], session):
    all_tag_names = {tag for item in data for tag in item.get(constants.tags, [])}
    return get_or_create_tags(user_id, session, all_tag_names)
