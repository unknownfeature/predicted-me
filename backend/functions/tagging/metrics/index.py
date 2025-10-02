import json
import os
from functools import reduce
from typing import List, Dict, Any

import boto3
from sqlalchemy import inspect, select, and_, insert
from sqlalchemy.orm import Session, selectinload

from backend.lib.db import Metric, Data, Tag
from backend.lib.func.tagging import Function
from backend.lib.util import get_or_create_tags, merge_tags
from shared.variables import Env

generative_model = os.getenv(Env.generative_model)
max_tokens = os.getenv(Env.max_tokens)

output_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {
                "type": "number",
                "description": "The original ID of the metric being tagged."
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": f"A list of 1 to 3 relevant tags. Max length per tag: {inspect(Tag).c.name.type.length} characters."
                }
            }
        },
        "required": ["id", "tags"]
    }
}

tagging_prompt = (
    "You are an expert taxonomy and categorization engine. Analyze the provided list of metrics and assign 1 to 3 "
    "relevant categories to each one from the allowed taxonomy. Your output must be ONLY a JSON array that "
    "strictly adheres to the provided schema.\n\n"
    f"**Output JSON Schema**:\n{json.dumps(output_schema, indent=3)}\n\n"
    "--- EXAMPLES ---\n"
    "Input Metrics:\n"
    "[\n"
    "  {\"id\": 1, \"name\": \"distance_run\", \"value\": 5, \"units\": \"miles\"},\n"
    "  {\"id\": 2, \"name\": \"apple_stock_price\", \"value\": 175.50, \"units\": \"USD\"}\n"
    "]\n"
    "Output:\n"
    "[\n"
    "  {\"id\": 1, \"tags\": [\"health_fitness\", \"activity\"]},\n"
    "  {\"id\": 2, \"tags\": [\"financial_wellbeing\"]}\n"
    "]\n"
    "--- END EXAMPLES ---\n\n"
    "**Metrics to Tag**:\n"
)


def text_supplier(session: Session, note_id, _):
    query = select(Metric).join(Data, Metric.data_points).where(and_([Data.note_id == note_id, not Metric.tagged]))

    untagged_metrics = session.scalars(query).all()

    if not untagged_metrics:
        print(f"No metrics to tag{note_id} are already tagged. Skipping.")
        return

    return (
        f"\n{json.dumps([{
            'id': m.id,
            'name': m.name,
            'units': m.units} for m in untagged_metrics
        ])}"
    )


def on_extracted_cb(session: Session, note_id: int, _: str, data: List[Dict[str, Any]]):
    merge_tags(session, data, lambda: select(Metric)
               .join(Metric.data_points)
               .where(
        and_(
            Metric.id.in_([item['id'] for item in data]),
            Data.note_id == note_id,
            Metric.tagged == False
        )
    )
               .options(selectinload(Metric.tags)))


tagging_function = Function(tagging_prompt, text_supplier, on_extracted_cb, generative_model,
                            int(max_tokens))


def handler(event, _):
    return tagging_function.handler(event, None)
