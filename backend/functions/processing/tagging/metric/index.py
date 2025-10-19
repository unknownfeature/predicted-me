import json
import os
from typing import List, Dict, Any

from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session, selectinload

from shared import constants
from backend.lib.db import Metric, Data, Tag, Note
from backend.lib.func.sqs import process_record_factory, Params, handler_factory, Model, MessageInput
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
    "relevant categories to each one. If you detect data with name which can be a food add 'Food' tag to it. If you detect somethind taht looks lilema supplement add 'Supplement' tag. and if you detect a medication add 'Medication' tag to it.  Your output must be ONLY a JSON array that "
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


def text_supplier(session: Session, message_input: MessageInput):
    if not message_input.note_id and not message_input.data_id:
        return None

    conditions = []
    if message_input.note_id:
        conditions.append(Data.note_id == message_input.note_id)
    if message_input.data_id:
        conditions.append(Data.id == message_input.data_id)
    conditions.append(Metric.tagged == False)

    query = select(Metric).join(Metric.data_points).where(and_(*conditions))

    untagged_metrics = session.scalars(query).unique().all()

    if not untagged_metrics:
        return

    return json.dumps([{
            constants.id: d.id,
            constants.name: d.display_name} for d in untagged_metrics
        ])



def on_response_from_model(session: Session, message_input: MessageInput, data: List[Dict[str, Any]]):
    if message_input.note_id:
       note = session.get(Note, message_input.note_id)
       add_tags(note.user_id, session, data, lambda: select(Metric)
                .join(Metric.data_points).where(and_(
           Metric.id.in_([item[constants.id] for item in data]),
           Data.note_id == message_input.note_id,
           Metric.tagged == False
       )
       ).options(selectinload(Metric.tags)))
    elif message_input.data_id:
        stmt = select(Metric).join(Metric.data_points).where(Data.id == message_input.data_id)
        metric = session.scalar(stmt)
        add_tags(metric.user_id, session, data, lambda:  select(Metric)
                .join(Metric.data_points).where(and_(
           Data.id  == message_input.data_id,
           Metric.tagged == False
        )).options(selectinload(Metric.tags)))

    else:
        raise ValueError('no metric id an no note id')  # should not happen
    session.commit()


handler = handler_factory(
    process_record_factory(Params(tagging_prompt, text_supplier, Model(generative_model), max_tokens), on_response_from_model))
