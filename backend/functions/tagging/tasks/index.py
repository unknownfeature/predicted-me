import json
import os
from typing import List, Dict, Any

import boto3
from sqlalchemy import inspect, select, and_, insert
from sqlalchemy.orm import session

from backend.lib.db import Tag, Task, Link
from backend.lib.func.tagging import Function
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

link_tagging_prompt = (
    "You are an expert taxonomy and categorization engine. Your job is to analyze a list of link descriptions and assign "
    "1 to 3 relevant categories to each one from the allowed taxonomy. "
    "Your output must be ONLY a JSON array that strictly adheres to the provided schema.\n\n"
    "**Allowed Taxonomy**:\n"
    "[TECHNOLOGY, NEWS, LIFESTYLE, SHOPPING, SOCIAL_MEDIA, EDUCATION, FINANCE, ENTERTAINMENT, FOOD_DRINK, HEALTH]\n\n"
    f"**Output JSON Schema**:\n{json.dumps(output_schema, indent=2)}\n\n"
    "--- EXAMPLES ---\n"
    "Input Links:\n"
    "[\n"
    "  {\"id\": 201, \"description\": \"A review of the latest smartphone releases for the year, comparing camera and battery life.\"},\n"
    "  {\"id\": 202, \"description\": \"Official page for Nike Air Max shoes. View the latest styles and purchase online.\"},\n"
    "  {\"id\": 203, \"description\": \"A simple recipe for making sourdough bread at home, with step-by-step instructions.\"}\n"
    "]\n"
    "Output:\n"
    "[\n"
    "  {\"id\": 201, \"tags\": [\"TECHNOLOGY\", \"NEWS\"]},\n"
    "  {\"id\": 202, \"tags\": [\"SHOPPING\", \"LIFESTYLE\"]},\n"
    "  {\"id\": 203, \"tags\": [\"FOOD_DRINK\", \"LIFESTYLE\"]}\n"
    "]\n"
    "--- END EXAMPLES ---\n\n"
    "**Links to Tag**:\n"
)

def text_supplier(sss: session, note_id, _):
    query = select(Link).where(and_([Link.note_id == note_id, not Link.tagged]))

    untagged_links = sss.scalars(query).all()

    if not untagged_links:
        print(f"No tasks to tag{note_id} are already tagged. Skipping.")
        return

    return (
        f"\n{json.dumps([{
            'id': m.id,
            'description': m.name} for m in untagged_links
        ])}"
    )


def on_extracted_cb(sss: session, note_id: int, origin: str, tags: List[Dict[str, Any]]):
    sss.execute((
        insert(Task.__table__)
        .values([d | {'note_id': note_id, 'origin': origin} for d in tags])

        .on_conflict_do_nothing(
            index_elements=['ulr']
        )
    ))
    # todo insertion logic
    #
    # if tags_to_insert:
    #     tag_insert_stmt = (
    #         insert(metrics_tags_association)
    #         .values(tags_to_insert)
    #         .prefix_with('IGNORE')
    #     )
    #     sss.execute(tag_insert_stmt)
    #     print(f"Attempted to insert {len(tags_to_insert)} unique metric-tag associations.")
    #
    # update_stmt = (
    #     update(Metrics)
    #     .where(Metrics.id.in_(metrics_to_update))
    #     .values(tagged=True)
    # )
    # sss.execute(update_stmt)
    pass


tagging_function = Function(tagging_prompt, text_supplier, on_extracted_cb, generative_model,
                            int(max_tokens))


def handler(event, _):
    return tagging_function.handler(event, None)
