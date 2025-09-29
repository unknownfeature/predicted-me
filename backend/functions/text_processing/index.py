import os
import json
import traceback
from typing import List, Dict, Any
from sqlalchemy import create_engine, insert, select
from sqlalchemy.dialects.mysql import insert as mysql_insert

from db import Metrics, Message, MetricOrigin
from db.util import begin_session
import boto3
from sqlalchemy import func

sns_client = boto3.client('sns')
sns_topic_arn = os.environ.get('TAGGING_TOPIC_ARN')

text_extraction_model = os.environ.get('TEXT_EXTRACTION_MODEL')

metrics_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string",
                     "description": "Normalized name of the metric (e.g., 'distance_run', 'calories_burned')"},
            "value": {"type": "number", "description": "The numeric value extracted."},
            "units": {"type": "string", "description": "The unit of measurement (e.g., 'miles', 'kcal', 'bpm')."}
        },
        "required": ["name", "value", "units"]
    }
}

prompt = ("You are an expert metric extraction bot. Analyze the text below and extract ALL quantifiable "
          "numeric metrics, including their unit. Output ONLY a JSON array that strictly adheres to the "
          "provided schema. If a metric cannot be found, do not include it. Ignore non-numeric qualitative adjectives.\n\n"
          f"**SCHEMA**:\n{json.dumps(metrics_schema)}\n\n")

bedrock_runtime = boto3.client('bedrock-runtime')

text_getters = {
    MetricOrigin.text.value: lambda x: x.text,
    MetricOrigin.audio_text.value: lambda x: x.audio_text,
    MetricOrigin.img_text.value: lambda x: x.img_text,
    MetricOrigin.img_desc.value: lambda x: x.image_description,

}


def process_record(session, record):
    sns_notification = json.loads(record['body'])
    payload = json.loads(sns_notification['Message'])
    message_id = payload.get('message_id')
    origin = payload.get('origin')

    if not message_id:
        print("Skipping record: message_id not found in payload.")
        return

    message_query = select(Message).where(Message.id == message_id)
    target_message = session.scalar(message_query)

    if not target_message:
        return

    text_content = text_getters[origin](target_message)

    if not text_content:
        print(f"Skipping Message ID {message_id}: No text or audio transcription to analyze.")
        return

    extracted_metrics = call_bedrock_for_metrics(text_content)

    if not extracted_metrics:
        print(f"No numeric metrics extracted by Bedrock for Message ID {message_id}.")
        return

    metrics_to_insert = [{
        'message_id': message_id,
        'name': metric.get('name'),
        'value': metric.get('value'),
        'units': metric.get('units'),
        'tagged': False,
        'origin': origin
    } for metric in extracted_metrics if 'name' in metric]

    if not metrics_to_insert:
        return

    upsert_stmt = (
        insert(Metrics.__table__)
        .values(metrics_to_insert)

        .on_duplicate_key_update(
            value=func.greatest(Metrics.__table__.c.value, mysql_insert.inserted.value),
            units=func.if_(
                Metrics.__table__.c.units.is_(None),
                mysql_insert.inserted.units,
                Metrics.__table__.c.units
            ),
            tagged=Metrics.__table__.c.tagged,
            origin=Metrics.__table__.c.origin
        )
    )
    session.execute(upsert_stmt)
    print(f"Successfully upserted {len(metrics_to_insert)} text metrics for ID {message_id}.")

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=json.dumps({
            'message_id': message_id,
        }),
        Subject='Media Processing Complete for Categorization'
    )


def call_bedrock_for_metrics(text_content: str) -> List[Dict[str, Any]]:
    try:
        response = bedrock_runtime.invoke_model(
            modelId=text_extraction_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt + (
                    f"TEXT FOR ANALYSIS: {text_content}"
                )}]}],
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


def handler(event, context):
    try:
        session = begin_session()

        for record in event['Records']:
            process_record(session, record)
        session.commit()
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        raise e
    finally:
        session.close()

    return {'statusCode': 200, 'body': f"Successfully processed {len(event['Records'])} SQS messages."}
