import json
import os
import traceback
from typing import Dict, Any, List

import boto3
from sqlalchemy import select, func, and_
from sqlalchemy.orm import session, joinedload

from backend.lib.db import Note, Tag, Metric, MetricOrigin, begin_session, get_utc_timestamp_int, Data
from backend.lib.util import seconds_in_day, get_user_id_from_event, get_ts_start_and_end

from shared.variables import Env

secrets_client = boto3.client('secretsmanager')
sns_client = boto3.client('sns')
sns_topic_arn = os.getenv(Env.text_processing_topic_arn)


# todo extract this function
def send_text_to_sns(text, note_id):
    if not text:
        return

    sns_payload = {
        'note_id': note_id,
        'origin': MetricOrigin.text
    }

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Note=json.dumps(sns_payload),
        Subject='Text ready for metrics extraction for Note ID {note_id} and origin {origin}.'
    )

    print(f"Sent SNS note for final categorization of Note ID {note_id}.")


def post(session: session, user_id: int, body: Dict[str, Any]) -> tuple[dict[str, Any], int]:
    new_note = Note(
        user_id=user_id,
        text=body.get('text'),
        image_key=body.get('image_key'),
        audio_key=body.get('audio_key'),
    )

    session.add(new_note)
    session.flush()

    return {
        'note_id': new_note.id,
        'time': new_note.time
    }, 201


def get(session: session, user_id: int, query_params: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
    start_time, end_time = get_ts_start_and_end(query_params)
    note_id = query_params.get('id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    metrics = query_params.get('metrics').split(',') if 'metrics' in query_params else []

    search_text = query_params.get('search_text')
    note_query = select(Note)
    conditions = [
        Note.user_id == user_id
    ]

    if not note_id:
        conditions.extend([Note.time >= start_time, Note.time <= end_time])
        if tags or metrics:
            note_query = note_query.join(Note.data_points).join(Data.metric)

        if tags:
            conditions.append(Metric.tags.any(Tag.name.in_(tags)))
        if metrics:
            conditions.append(Metric.name.in_(metrics))

        if search_text:
            search_columns = Note.text, Note.image_text, Note.image_description, Note.audio_text

            full_text_condition = func.match(*search_columns).against(
                search_text,
                natural=True
            )

            conditions.append(full_text_condition)
    else:
        conditions.append(Note.id == int(note_id))

    note_query = note_query.where(
        and_(*conditions)
    ).order_by(Note.time.desc())

    notes = [{
        'id': note.id,
        'text': note.text,
        'time': note.time.isoformat(),
        'image_key': note.image_key,
        'audio_key': note.audio_key,
        'image_described': note.image_described,
        'audio_transcribed': note.audio_transcribed,
        'image_text': note.image_text,
        'image_description': note.audio_transcribed,
        'audio_text': note.image_text,

    }
        for note in session.scalars(note_query).all()]

    return notes, 200


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:
        session = begin_session()

        user_id = get_user_id_from_event(event, session)

        http_method = event['httpMethod']

        if http_method == 'POST':
            body = json.loads(event['body'])
            response_data, status_code = post(session, user_id, body)
            session.commit()
            send_text_to_sns(body.get('text'), response_data.get('note_id'))

        elif http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            response_data, status_code = get(session, user_id, query_params)

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'})}

        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }

    except Exception:
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}

    finally:
        if session:
            session.close()
