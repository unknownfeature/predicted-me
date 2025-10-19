import json
import os
from typing import List, Dict, Any

from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session, selectinload

from shared import constants
from backend.lib.db import Tag, Task, Note, Occurrence
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
                "description": "The original ID of the task being tagged."
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
    "You are an expert taxonomy and categorization engine. Your job is to analyze a list of task descriptions and assign "
    "1 to 3 relevant categories to each one from the allowed taxonomy. "
    "Your output must be ONLY a JSON array that strictly adheres to the provided db.\n\n"

    f"**Output JSON Schema**:\n{json.dumps(output_schema, indent=3)}\n\n"
    "--- EXAMPLES ---\n"
    "Input task descriptions:\n"
    "[\n"
    "  {\"id\": 201, \"description\": \"A review of the latest smartphone releases for the year, comparing camera and battery life.\"},\n"
    "  {\"id\": 202, \"description\": \"Official page for Nike Air Max shoes. View the latest styles and purchase online.\"},\n"
    "  {\"id\": 203, \"description\": \"A simple recipe for making sourdough bread at home, with step-by-step instructions.\"}\n"
    "]\n"
    "Output:\n"
    "[\n"
    "  {\"id\": 201, \"tags\": [\"Technology\", \"News\"]},\n"
    "  {\"id\": 202, \"tags\": [\"Shopping\", \"Lifestyle\"]},\n"
    "  {\"id\": 203, \"tags\": [\"Food drink\", \"Lifestyle\"]}\n"
    "]\n"
    "--- END EXAMPLES ---\n\n"
    "**Tasks to Tag**:\n"
)


def text_supplier(session: Session, message_input: MessageInput):
    if not message_input.note_id and not message_input.occurrence_id:
        return None

    conditions = []
    if message_input.note_id:
        conditions.append(Task.note_id == message_input.note_id)
    if message_input.occurrence_id:
        conditions.append(Task.id == message_input.occurrence_id)
    conditions.append(Task.tagged == False)
    query = select(Task).where(and_(*conditions))

    untagged_tasks = session.scalars(query).unique().all()

    if not untagged_tasks:
        return

    return json.dumps([{
            constants.id: t.id,
            constants.description: t.description} for t in untagged_tasks
        ])


def on_response_from_model(session: Session, message_input: MessageInput, data: List[Dict[str, Any]]):
    if message_input.note_id:
       note = session.get(Note, message_input.note_id)
       add_tags(note.user_id, session, data, lambda: select(Task).where(
           and_(
               Task.id.in_([item[constants.id] for item in data]),
               Task.tagged == False,
               Task.note_id == message_input.note_id
           )
       ).options(selectinload(Task.tags)))
    elif message_input.occurrence_id:
        stmt = select(Task).join(Task.occurrences).where(Occurrence.id == message_input.occurrence_id)
        task = session.scalar(stmt)
        add_tags(task.user_id, session, data, lambda: select(Task).join(Task.occurrences).where(
            and_(
                Task.tagged == False,
                Occurrence.id == message_input.occurrence_id
            )
        ).options(selectinload(Task.tags)))

    else:
        raise ValueError('no task id and no note id')  # should not happen

    session.commit()


handler = handler_factory(
    process_record_factory(Params(tagging_prompt, text_supplier, Model(generative_model), max_tokens), on_response_from_model))
