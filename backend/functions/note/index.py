import json
import os
import traceback
from typing import Dict, Any, List

import boto3
from sqlalchemy import select, func, and_
from sqlalchemy.orm import session

from backend.lib.db import Note, MetricOrigin, begin_session, get_utc_timestamp_int
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


def post(session: session, user_id: int, body: Dict[str, Any]) -> Dict[str, Any]:
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
    }


def get(session: session, user_id: int, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    start_time, end_time = get_ts_start_and_end(query_params)

    note_id = query_params.get('id')
    search_text = query_params.get('search_text')

    conditions = [
        Note.user_id == user_id
    ]

    if not note_id:
        conditions.append(Note.time >= start_time)
        conditions.append(Note.time <= end_time)
    else:
        conditions.append(Note.id == int(note_id))

    if search_text:
        search_columns = Note.text, Note.image_text, Note.image_description, Note.audio_text

        full_text_condition = func.match(*search_columns).against(
            search_text,
            natural=True
        )

        conditions.append(full_text_condition)

    note_query = select(Note).where(
        and_(*conditions)
    ).order_by(Note.time.desc())

    notes = [{
        'note_id': note.id,
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

    return notes


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:
        session = begin_session()

        user_id = get_user_id_from_event(event, session)

        http_method = event['httpMethod']

        if http_method == 'POST':
            body = json.loads(event['body'])
            response_data = post(session, user_id, body)
            status_code = 201
            session.commit()
            send_text_to_sns(body.get('text'), response_data.get('note_id'))

        elif http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            response_data = get(session, user_id, query_params)
            status_code = 200

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'})}

        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }

    except Exception as e:
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}

    finally:
        if session:
            session.close()
