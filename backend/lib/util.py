import json
import traceback
import uuid
from enum import Enum
from typing import Dict, Any, List, Set, Callable, Tuple

import boto3
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from backend.lib.db import User, get_utc_timestamp, Origin, Tag, Metric, normalize_identifier, Task

seconds_in_day = 24 * 60 * 60

text_getters = {
    Origin.text.value: lambda x: x.text,
    Origin.audio_text.value: lambda x: x.audio_text,
    Origin.img_text.value: lambda x: x.img_text,
    Origin.img_desc.value: lambda x: x.image_description,

}


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

def get_or_create_tasks(session: Session, summary_to_display_summary: Dict[str, str], user_id: int) -> Dict[str, Task]:
    existing =  {m.summary: m for m in
            session.scalars(select(Task).where(and_([Task.user_id == user_id, Task.summary.in_(summary_to_display_summary.keys())]))).all()}
    non_existing = set(summary_to_display_summary.keys()).intersection(existing.keys())
    if non_existing:
        results = {}
        for summary in non_existing:
            new_metrics = Task(summary=summary, user_id=user_id, display_summary=summary_to_display_summary[summary])
            session.add(new_metrics)
            results[summary] = new_metrics
        session.flush()
        return results | existing
    return existing

def get_or_create_metrics(session: Session, names_to_display_names: Dict[str, str], user_id: int) -> Dict[str, Metric]:
    existing =  {m.name: m for m in
            session.scalars(select(Metric).where(and_([Metric.user_id == user_id, Metric.name.in_(names_to_display_names.keys())]))).all()}
    non_existing = set(names_to_display_names.keys()).intersection(existing.keys())
    if non_existing:
        results = {}
        for name in non_existing:
            new_metrics = Metric(name=name, user_id=user_id, display_name=names_to_display_names[name])
            session.add(new_metrics)
            results[name] = new_metrics
        session.flush()
        return results | existing
    return existing

def get_user_ids_from_event(event: Dict[str, Any], session: Session) -> Tuple[int, str]:
    external_user = event['requestContext']['authorizer']['jwt']['claims']['username']
    user_query = select(User.id).where(User.external_id == external_user)
    user = session.execute(user_query).first()

    return user.id if user else None, external_user

def get_ts_start_and_end(query_params):
    start_param = query_params.get('start')
    end_param = query_params.get('end')

    if not start_param and end_param:
        end_time = int(end_param)
        start_time = end_time - seconds_in_day
    elif start_param and not end_param:
        start_time = int(start_param)
        end_time =  get_utc_timestamp()
    elif start_param and end_param:
        start_time = int(start_param)
        end_time = int(end_param)
    else:
        now_utc = get_utc_timestamp()
        start_time = now_utc - seconds_in_day
        end_time = now_utc

    if start_time >= end_time:
        raise ValueError('Start time must be before end time.')
    return start_time, end_time

def call_bedrock(model: str, prompt: str, text_content: str, max_tokens = 1024) -> List[Dict[str, Any]]:
    try:
        bedrock_runtime = boto3.client('bedrock-runtime')

        id = uuid.uuid4().hex
        response = bedrock_runtime.invoke_model(
            modelId=model,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': max_tokens,
                'notes': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt + (
                    f'TEXT FOR ANALYSIS:    ---START_USER_INPUT {id} ---  {text_content} ---END_USER_INPUT  {id} ---'
                ) if text_content else ''}]}],
            })
        )

        response_body = json.loads(response['body'].read())
        metrics_json_str = response_body['content'][0]['text'].strip()

        if metrics_json_str.startswith('```'):
            metrics_json_str = metrics_json_str.split('\n', 1)[-1].strip('`')

        return json.loads(metrics_json_str)

    except Exception as e:
        traceback.print_exc()
        raise e


def get_or_create_tags(session: Session, tag_names: Set[str]) -> Dict[str, Tag]:
    if not tag_names:
        return {}

    stmt = select(Tag).where(Tag.name.in_(tag_names))
    existing_tags = session.scalars(stmt).all()
    existing_tags_dict = {tag.name: tag for tag in existing_tags}
    new_tags = {t.lower(): Tag(name = t) for t in tag_names if t not in existing_tags_dict}


    if new_tags:
        session.add_all(new_tags.values())
        session.flush()

    return existing_tags_dict | new_tags

def merge_tags(session: Session, data: List[Dict[str, Any]], stmt_supplier: Callable[[], Any]):
    if not data:
        return

    tag_map = get_tags_map_for_update(data, session)
    data_map = {item['id']: item.get('tags', []) for item in data}

    entities_to_update = session.scalars(stmt_supplier()).unique().all()
    for entity in entities_to_update:
        entity.tags.clear()
        entity.tags.extend([tag_map[tag_name.lower()] for tag_name in data_map[entity.id] if
                            tag_name.lower() not in {tag.name for tag in entity.tags}])
        entity.tagged = True


def get_tags_map_for_update(data: List[Dict[str, str]], session):
    all_tag_names = {tag.lower() for item in data for tag in item.get('tags', [])}
    tag_map = get_or_create_tags(session, all_tag_names)
    return tag_map