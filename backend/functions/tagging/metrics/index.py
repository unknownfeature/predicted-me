import json
import os
from typing import List, Dict, Any

from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session, selectinload

from backend.lib.db import Metric, Data, Tag
from backend.lib.func.tagging import process_record_factory, Params
from backend.lib.func.sqs import handler_factory
from backend.lib.util import merge_tags
from shared.variables import Env

generative_model = os.getenv(Env.generative_model)
max_tokens = int(os.getenv(Env.max_tokens))

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
    query = select(Data).join(Metric.data_points).where(and_([Data.note_id == note_id, not Metric.tagged]))

    untagged_data = session.scalars(query).all()

    if not untagged_data:
        print(f"No metrics to tag{note_id} are already tagged. Skipping.")
        return

    # todo could be duplicates? not sure
    return (
        f"\n{json.dumps([{
            'id': d.metric_id,
            'name': d.metric.name,
            'units': d.units} for d in untagged_data
        ])}"
    )


def on_extracted_cb(session: Session, note_id: int, _: str, data: List[Dict[str, Any]]):
    merge_tags(session, data, lambda: select(Metric)
               .join(Metric.data_points).where(and_(
        Metric.id.in_([item['id'] for item in data]),
        Data.note_id == note_id,
        Metric.tagged == False
    )
    ).options(selectinload(Metric.tags)))


handler = handler_factory(
    process_record_factory(Params(tagging_prompt, text_supplier, generative_model, max_tokens), on_extracted_cb))
