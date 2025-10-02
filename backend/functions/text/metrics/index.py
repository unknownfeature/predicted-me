import json
import os
from typing import List, Dict, Any

import boto3
from sqlalchemy import func
from sqlalchemy import insert, select, bindparam, inspect

from backend.lib.db import Metric, Data, Note
from backend.lib.func.text_extraction import Function
from backend.tests.db import Session
from shared.variables import Env

sns_client = boto3.client('sns')
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)
max_tokens =  os.getenv(Env.max_tokens)


metrics_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": f"Normalized name of the metric (e.g., 'distance_run', 'heart_rate'). Max length: {inspect(Metric).c.name.type.length} characters."
            },
            "value": {
                "type": "number",
                "description": "The numeric value extracted."
            },
            "units": {
                "type": "string",
                "description": f"The unit of measurement (e.g., 'miles', 'kcal', 'bpm'). If no units are mentioned, use a standard unit or 'unknown'. Max length: {inspect(Data).c.units.type.length} characters."
            }
        },
        "required": ["name", "value", "units"]
    }
}

prompt = ("You are an expert metric extraction bot. Analyze the text below and extract all quantifiable "
          "numeric metrics, including their value and unit. Normalize the metric name into a snake_case format. "
          "Your output must be ONLY a JSON array that strictly adheres to the provided schema. "
          "If no metrics are found, output an empty array []. "
          "Ignore non-numeric qualitative adjectives, links, and tasks.\n\n"
          f"**JSON Schema**:\n{json.dumps(metrics_schema, indent=3)}\n\n"
          "--- EXAMPLES ---\n"
          "Text: 'I ran 5 miles today and my heart rate was 120bpm. It felt great!'\n"
          "Output: [{\"name\": \"distance_run\", \"value\": 5, \"units\": \"miles\"}, {\"name\": \"heart_rate\", \"value\": 120, \"units\": \"bpm\"}]\n\n"
          "Text: 'Weight this morning was 185.3 lbs.'\n"
          "Output: [{\"name\": \"weight\", \"value\": 185.3, \"units\": \"lbs\"}]\n"
          "--- END EXAMPLES ---\n\n"
          "**Text to Analyze**:\n")

def on_extracted_cb(session: Session, target_note: Note, origin: str, data: List[Dict[str, Any]]) -> None:    # todo review this, look suspicious
    data_and_metrics = [{
        'note_id': target_note.id,
        'name': metric.get('name').lower(),
        'value': metric.get('value'),
        'units': metric.get('units'),
        'time': target_note.time,
        'origin': origin
    } for metric in data if 'name' in metric]

    if not data_and_metrics:
        return

    upsert_stmt = (
        insert(Metric.__table__)
        .values(data_and_metrics)

        .on_conflict_do_nothing(
            index_elements=['name']
        )
    )
    session.execute(upsert_stmt)
    select_columns = [
        Metric.__table__.c.id,
        bindparam('note_id', value=target_note.id),
        bindparam('value'),
        bindparam('units'),
        bindparam('origin'),
        bindparam('time')
    ]

    case_insensitive_join = func.lower(Metric.__table__.c.name) == func.lower(bindparam('name'))

    subquery_select = (
        select(*select_columns)
        .select_from(Metric.__table__)
        .where(case_insensitive_join)
    )

    insert_data_stmt = (
        insert(Data.__table__)
        .from_select(
            ['metric_id', 'note_id', 'value', 'units', 'origin'],
            subquery_select
        )
    )

    session.execute(insert_data_stmt, data_and_metrics)

    sns_client.publish(
        TopicArn=tagging_topic_arn,
        Note=json.dumps({
            'note_id': target_note.id,
        }),
        Subject='Extracted metrics ready for tagging'
    )

text_processing_function = Function(prompt, on_extracted_cb, text_extraction_model, int(max_tokens))

def handler(event, _):
    return text_processing_function.handler(event, None)
