import json
import os
import traceback
import uuid
from typing import List, Dict, Any

import boto3

from backend.lib.db import Metrics, Note, MetricOrigin, Data
from backend.lib.db.util import begin_session
from sqlalchemy import func
from sqlalchemy import insert, select, bindparam

from shared.variables import Env

sns_client = boto3.client('sns')
sns_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)

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
    payload = json.loads(sns_notification['Note'])
    note_id = payload.get('note_id')
    origin = payload.get('origin')

    if not note_id:
        print("Skipping record: note_id not found in payload.")
        return

    note_query = select(Note).where(Note.id == note_id)
    target_note = session.scalar(note_query)

    if not target_note:
        return

    text_content = text_getters[origin](target_note)

    if not text_content:
        print(f"Skipping Note ID {note_id}: No text or audio transcription to analyze.")
        return

    extracted_metrics = call_bedrock_for_metrics(text_content)

    if not extracted_metrics:
        print(f"No numeric metrics extracted by Bedrock for Note ID {note_id}.")
        return

    data_and_metrics = [{
        'note_id': note_id,
        'name': metric.get('name'),
        'value': metric.get('value'),
        'units': metric.get('units'),
        'time': target_note.time,
        'tagged': False,
        'origin': origin
    } for metric in extracted_metrics if 'name' in metric]

    if not data_and_metrics:
        return

    upsert_stmt = (
        insert(Metrics.__table__)
        .values(data_and_metrics)

        .on_duplicate_key_update(
        id=Metrics.__table__.c.id
    )
    )
    session.execute(upsert_stmt)
    select_columns = [
        Metrics.__table__.c.id,
        bindparam('note_id', value=note_id),
        bindparam('value'),
        bindparam('units'),
        bindparam('origin'),
        bindparam('time')
    ]

    case_insensitive_join = func.lower(Metrics.__table__.c.name) == func.lower(bindparam('name'))

    subquery_select = (
        select(*select_columns)
        .select_from(Metrics.__table__)
        .where(case_insensitive_join)
    )

    insert_data_stmt = (
        insert(Data.__table__)
        .from_select(
            ['metrics_id', 'note_id', 'value', 'units', 'origin'],
            subquery_select
        )
    )

    session.execute(insert_data_stmt, data_and_metrics)

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Note=json.dumps({
            'note_id': note_id,
        }),
        Subject='Media Processing Complete for Categorization'
    )


def call_bedrock_for_metrics(text_content: str) -> List[Dict[str, Any]]:
    try:
        id = uuid.uuid4().hex
        response = bedrock_runtime.invoke_model(
            modelId=text_extraction_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "notes": [{"role": "user", "content": [{"type": "text", "text": prompt + (
                    f"TEXT FOR ANALYSIS:    ---START_USER_INPUT {id} ---  {text_content} ---END_USER_INPUT  {id} ---"
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

    return {'statusCode': 200, 'body': f"Successfully processed {len(event['Records'])} SQS notes."}
