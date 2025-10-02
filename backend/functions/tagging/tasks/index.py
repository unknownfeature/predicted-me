import json
import os
from typing import List, Dict, Any

import boto3
from sqlalchemy import inspect, select, and_, insert
from sqlalchemy.orm import Session, selectinload

from backend.lib.db import Tag, Task, Link
from backend.lib.func.tagging import Function
from backend.lib.util import get_or_create_tags, merge_tags
from shared.variables import Env

bedrock_runtime = boto3.client('bedrock-runtime')

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
    "You are an expert taxonomy and categorization engine. Your job is to analyze a list of link descriptions and assign "
    "1 to 3 relevant categories to each one from the allowed taxonomy. "
    "Your output must be ONLY a JSON array that strictly adheres to the provided schema.\n\n"

    f"**Output JSON Schema**:\n{json.dumps(output_schema, indent=3)}\n\n"
    "--- EXAMPLES ---\n"
    "Input Links:\n"
    "[\n"
    "  {\"id\": 201, \"description\": \"A review of the latest smartphone releases for the year, comparing camera and battery life.\"},\n"
    "  {\"id\": 202, \"description\": \"Official page for Nike Air Max shoes. View the latest styles and purchase online.\"},\n"
    "  {\"id\": 203, \"description\": \"A simple recipe for making sourdough bread at home, with step-by-step instructions.\"}\n"
    "]\n"
    "Output:\n"
    "[\n"
    "  {\"id\": 201, \"tags\": [\"technology\", \"news\"]},\n"
    "  {\"id\": 202, \"tags\": [\"shopping\", \"lifestyle\"]},\n"
    "  {\"id\": 203, \"tags\": [\"food_drink\", \"lifestyle\"]}\n"
    "]\n"
    "--- END EXAMPLES ---\n\n"
    "**Links to Tag**:\n"
)


def text_supplier(session: Session, note_id, _):
    query = select(Link).where(and_([Link.note_id == note_id, not Link.tagged]))

    untagged_links = session.scalars(query).all()

    if not untagged_links:
        print(f"No tasks to tag{note_id} are already tagged. Skipping.")
        return

    return (
        f"\n{json.dumps([{
            'id': m.id,
            'description': m.name} for m in untagged_links
        ])}"
    )


def on_extracted_cb(session: Session, note_id: int, _: str, data: List[Dict[str, Any]]):
    merge_tags(session, data, lambda: select(Task)

               .where(
        and_(
            Task.id.in_([item['id'] for item in data]),
            Task.tagged == False,
            Task.note_id == note_id
        )
    )
               .options(selectinload(Task.tags)))


tagging_function = Function(tagging_prompt, text_supplier, on_extracted_cb, generative_model,
                            int(max_tokens))


def handler(event, _):
    return tagging_function.handler(event, None)
