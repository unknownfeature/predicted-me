import os
import json
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import boto3
from sqlalchemy.orm import joinedload, session
from sqlalchemy import create_engine, select, func, or_, and_

from backend.lib.db.mapping import User, Message, Data, Metrics, MetricOrigin
from backend.lib.db.util import begin_session

secrets_client = boto3.client('secretsmanager')
sns_client = boto3.client('sns')
sns_topic_arn = os.getenv(Env.text_processing_topic_arn)


# todo extract this function
def send_text_to_sns(text, message_id):
    if not text:
        return

    sns_payload = {
        'message_id': message_id,
        'origin': MetricOrigin.text
    }

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=json.dumps(sns_payload),
        Subject='Text ready for metrics extraction for Message ID {message_id} and origin {origin}.'
    )

    print(f"Sent SNS message for final categorization of Message ID {message_id}.")


def get_user_id_from_external_id(session: session, external_id: str) -> int:
    user_query = select(User.id).where(User.external_id == external_id)
    return session.scalar(user_query)


def get_data_for_message(message_id: int, session: session) -> List[Dict[str, Any]]:
    data_query = select(Data).options(joinedload(Data.metric_type)).where(
        Data.message_id == message_id
    )
    data_points = session.scalars(data_query).all()

    results = []
    for dp in data_points:
        # Check if the metric definition exists
        metric = dp.metric_type

        results.append({
            'data_id': dp.id,
            'value': float(dp.value) if dp.value is not None else None,
            'units': dp.units,
            'origin': dp.origin.value,
            'metric': {
                'id': metric.id,
                'name': metric.name,
                'tags': [tag for tag in metric.tags]  # Tags are strings in the association table
            }
        })
    return results


def handle_post(session: session, user_id: int, body: Dict[str, Any]) -> Dict[str, Any]:
    new_message = Message(
        user_id=user_id,
        text=body.get('text'),
        image_key=body.get('image_key'),
        audio_key=body.get('audio_key'),
    )

    session.add(new_message)
    session.flush()

    return {
        'message_id': new_message.id,
        'time': new_message.time.isoformat()
    }


def handle_get(session: session, user_id: int, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    hours_ago = int(query_params.get('hours_ago', 24))
    message_id = int(query_params.get('id'))
    start_time = now - timedelta(hours=hours_ago)

    conditions = [
        Message.user_id == user_id
    ]

    if not message_id:
        conditions.append(Message.time >= start_time)
    else:
        conditions.append(Message.id == int(message_id))

    message_query = select(Message).where(
        and_(*conditions)
    ).order_by(Message.time.desc())

    messages = [{
        'message_id': message.id,
        'text': message.text,
        'time': message.time.isoformat(),
        'image_key': message.image_key,
        'audio_key': message.audio_key,
        'image_described': message.image_described,
        'audio_transcribed': message.audio_transcribed,
        'image_text': message.image_text,
        'image_description': message.audio_transcribed,
        'audio_text': message.image_text,

    }
        for message in session.scalars(message_query).all()]

    return_data_per_message = query_params.get('return_data_per_message', 'false').lower() == 'true'

    results = []
    for message in messages:
        message_dict = {
            'message_id': message.id,
            'text': message.text,
            'time': message.time.isoformat(),
            'image_key': message.image_key
        }

        results.append(message_dict)

    return results


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:
        session = begin_session()
        user_query = select(User.id).where(
            User.external_id == event['requestContext']['authorizer']['jwt']['claims']['username'])
        user_id = session.scalar(user_query)

        http_method = event['httpMethod']

        if http_method == 'POST':
            body = json.loads(event['body'])
            response_data = handle_post(session, user_id, body)
            status_code = 201
            session.commit()
            send_text_to_sns(body.get('text'), response_data.get('message_id'))

        elif http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            response_data = handle_get(session, user_id, query_params)
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
