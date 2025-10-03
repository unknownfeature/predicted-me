import json
import os
from typing import List, Dict, Any

import boto3
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, bindparam, inspect, func

from backend.lib.db import Metric, Data, Note
from backend.lib.func.sqs import handler_factory
from backend.lib.func.tagging import Params, process_record_factory
from backend.lib.func.text import note_text_supplier
from shared.variables import Env

sns_client = boto3.client('sns')
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

generative_model = os.getenv(Env.generative_model)
max_tokens =  int(os.getenv(Env.max_tokens))


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

def on_extracted_cb(session: Session, note_id: int, origin: str, data: List[Dict[str, Any]]) -> None:
    # todo review this, look suspicious
    note_query = select(Note).where(Note.id == note_id)
    target_note = session.scalar(note_query)

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

handler = handler_factory(
    process_record_factory(Params(prompt, note_text_supplier, generative_model, max_tokens), on_extracted_cb))
