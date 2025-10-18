import json
import os
from typing import List, Dict, Any

from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session, selectinload

from shared import constants
from backend.lib.db import Metric, Data, Tag, Note
from backend.lib.func.sqs import process_record_factory, Params, handler_factory, Model
from backend.lib.util import add_tags
from shared.constants import default_max_tokens
from shared.variables import *

generative_model = os.getenv(generative_model)
max_tokens = int(os.getenv(max_tokens, default_max_tokens))

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
                    "description": f"A list of 1 to 3 relevant tags with human readable names. Make sure to only use nouns and adjectives. Max length per tag: {inspect(Tag).c.name.type.length} characters."
                }
            }
        },
        "required": ["id", "tags"]
    }
}

tagging_prompt = (
    "You are an expert taxonomy and categorization engine. Analyze the provided list of metrics and assign 1 to 3 "
    "relevant categories to each one from the allowed taxonomy. Your output must be ONLY a JSON array that "
    "strictly adheres to the provided db.\n\n"
    f"**Output JSON Schema**:\n{json.dumps(output_schema, indent=3)}\n\n"
    "--- EXAMPLES ---\n"
    "Input Metrics:\n"
    "[\n"
    "  {\"id\": 1, \"name\": \"Distance run\", \"value\": 5, \"units\": \"miles\"},\n"
    "  {\"id\": 2, \"name\": \"Apple stock proces\", \"value\": 175.50, \"units\": \"USD\"}\n"
    "]\n"
    "Output:\n"
    "[\n"
    "  {\"id\": 1, \"tags\": [\"Health fittness\", \"activity\"]},\n"
    "  {\"id\": 2, \"tags\": [\"Financial wellbeing\"]}\n"
    "]\n"
    "--- END EXAMPLES ---\n\n"
    "**Metrics to Tag**:\n"
)


def text_supplier(session: Session, note_id, _):
    query = select(Metric).join(Metric.data_points).where(and_(Data.note_id == note_id,  Metric.tagged == False))

    untagged_metrics = session.scalars(query).unique().all()

    if not untagged_metrics:
        print(f"No metrics to tag{note_id} are already tagged. Skipping.")
        return

    # todo could be duplicates? not sure
    return (
        f"\n{json.dumps([{
            constants.id: d.id,
            constants.name: d.display_name} for d in untagged_metrics
        ])}"
    )


def on_response_from_model(session: Session, note_id: int, _: str, data: List[Dict[str, Any]]):
    note = session.get(Note, note_id)
    add_tags(note.user_id, session, data, lambda: select(Metric)
             .join(Metric.data_points).where(and_(
        Metric.id.in_([item[constants.id] for item in data]),
        Data.note_id == note_id,
        Metric.tagged == False
    )
    ).options(selectinload(Metric.tags)))
    session.commit()


handler = handler_factory(
    process_record_factory(Params(tagging_prompt, text_supplier, Model(generative_model), max_tokens), on_response_from_model))
