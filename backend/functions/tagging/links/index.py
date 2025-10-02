import json
import os
from typing import List, Dict, Any

from sqlalchemy import select, inspect, and_
from sqlalchemy.orm import Session, selectinload

from backend.lib.func.tagging import Function
from backend.lib.util import merge_tags
from shared.variables import Env
from backend.lib.db import Tag, Link

generative_model = os.getenv(Env.generative_model)
max_tokens =  os.getenv(Env.max_tokens)

output_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {
                "type": "number",
                "description": "The original ID of the link being tagged."
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

    untagged_tasks = session.scalars(query).all()

    if not untagged_tasks:
        print(f"No tasks to tag{note_id} are already tagged. Skipping.")
        return

    return (
        f"\n{json.dumps([{
            'id': m.id,
            'description': m.name} for m in untagged_tasks
        ])}"
    )



def on_extracted_cb(session: Session, note_id: int, _: str, data: List[Dict[str, Any]]):
    merge_tags(session, data, lambda: select(Link)

               .where(
        and_(
            Link.id.in_([item['id'] for item in data]),
            Link.tagged == False,
            Link.note_id == note_id
        )
    )
               .options(selectinload(Link.tags)))


tagging_function = Function(tagging_prompt, text_supplier, on_extracted_cb, generative_model,
                            int(max_tokens))


def handler(event, _):
    return tagging_function.handler(event, None)