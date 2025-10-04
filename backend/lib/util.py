import json
import traceback
import uuid
from enum import Enum
from typing import Dict, Any, List, Set, Callable, Tuple

import boto3
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.lib.db import User, get_utc_timestamp_int, MetricOrigin, Tag

seconds_in_day = 24 * 60 * 60

text_getters = {
    MetricOrigin.text.value: lambda x: x.text,
    MetricOrigin.audio_text.value: lambda x: x.audio_text,
    MetricOrigin.img_text.value: lambda x: x.img_text,
    MetricOrigin.img_desc.value: lambda x: x.image_description,

}


class HttpMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'

def get_user_ids_from_event(event: Dict[str, Any], session: Session) -> Tuple[int, str]:
    external_user = event['requestContext']['authorizer']['jwt']['claims']['username']
    user_query = select(User.id).where(User.external_id == external_user)
    user = session.scalar(user_query).first()
    return user.id if user else None, external_user

def get_ts_start_and_end(query_params):
    now_utc = get_utc_timestamp_int()
    start_time = int(query_params.get('start_ts')) if 'start_ts' in query_params else (now_utc - seconds_in_day)
    end_time = int(query_params.get('end_ts')) if 'end_ts' in query_params else now_utc
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

    all_tag_names = {tag.lower() for item in data for tag in item.get('tags', [])}
    tag_map = get_or_create_tags(session, all_tag_names)
    data_map = {item['id']: item.get('tags', []) for item in data}

    entities_to_update = session.scalars(stmt_supplier()).unique().all()
    for entity in entities_to_update:
        entity.tags.extend([tag_map[tag_name.lower()] for tag_name in data_map[entity.id] if
                            tag_name.lower() not in {tag.name for tag in entity.tags}])
        entity.tagged = True