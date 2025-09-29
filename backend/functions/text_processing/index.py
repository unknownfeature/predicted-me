import os
import json
import traceback
from typing import List, Dict, Any
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, insert, select

from lib.db import Metrics, Message, MetricOrigin
from lib.db.util import begin_session
import boto3


TEXT_EXTRACTION_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"

bedrock_runtime = boto3.client('bedrock-runtime')

def call_bedrock_for_metrics(text_content: str) -> List[Dict[str, Any]]:

    METRICS_SCHEMA = {
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

    prompt = (
        "You are an expert metric extraction bot. Analyze the text below and extract ALL quantifiable "
        "numeric metrics, including their unit. Output ONLY a JSON array that strictly adheres to the "
        "provided schema. If a metric cannot be found, do not include it. Ignore non-numeric qualitative adjectives.\n\n"
        f"TEXT FOR ANALYSIS: {text_content}"
    )

    try:
        response = bedrock_runtime.invoke_model(
            modelId=TEXT_EXTRACTION_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            })
        )

        response_body = json.loads(response['body'].read())
        metrics_json_str = response_body['content'][0]['text'].strip()

        if metrics_json_str.startswith('```'):
            metrics_json_str = metrics_json_str.split('\n', 1)[-1].strip('`')

        return json.loads(metrics_json_str)

    except Exception as e:
        print(f"Bedrock structured extraction failed: {e}")
        return []


def handler(event, context):
    session = begin_session()

    try:
        for record in event['Records']:
            sns_notification = json.loads(record['body'])

            payload = json.loads(sns_notification['Message'])
            message_id = payload.get('message_id')
            origin = payload.get('origin')

            if not message_id:
                print("Skipping record: message_id not found in payload.")
                continue

            print(f"Processing text metrics for Message ID: {message_id}")

            message_query = select(Message).where(Message.id == message_id)
            target_message = session.scalar(message_query)

            if not target_message:
                print(f"Skipping Message ID {message_id}: Message record not found in DB.")
                continue

            text_content = target_message.text or target_message.audio_text

            if not text_content:
                print(f"Skipping Message ID {message_id}: No text or audio transcription to analyze.")
                continue

            extracted_metrics = call_bedrock_for_metrics(text_content)

            if not extracted_metrics:
                print(f"No numeric metrics extracted by Bedrock for Message ID {message_id}.")
                continue

            # 3. Prepare and Insert Metrics
            metrics_to_insert = []
            for metric in extracted_metrics:
                if 'name' not in metric:
                    continue
                metrics_to_insert.append({
                    'message_id': message_id,
                    'normalized_name': metric.get('name'),
                    'original_name': metric.get('name'),
                    'value': metric.get('value'),
                    'units': metric.get('units'),
                    'tagged': False,
                    'origin': origin
                })

            if metrics_to_insert:
                insert_metrics_stmt = insert(Metrics.__table__).values(metrics_to_insert)
                session.execute(insert_metrics_stmt)
                print(f"Successfully inserted {len(metrics_to_insert)} metrics for Message ID {message_id}.")

        session.commit()

    except Exception as e:
        session.rollback()
        print(f"FATAL ERROR during transaction: {e}")
        traceback.print_exc()
        raise e

    finally:
        session.close()

    return {'statusCode': 200, 'body': f"Successfully processed {len(event['Records'])} SQS messages."}