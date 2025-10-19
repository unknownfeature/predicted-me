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
                "description": "The original ID of the food, medication or supplement item being analyzed."
            },
            "nutrients": {
                "type": "array",
                "description": "A comprehensive list of all major nutrients, vitamins, and minerals.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Human-readable name of the nutrient (e.g., 'Calories', 'Saturated Fat', 'Vitamin C')."
                        },
                        "value": {
                            "type": "number",
                            "description": "The estimated numeric value for that nutrient."
                        },
                        "units": {
                            "type": "string",
                            "description": "e.g., 'kcal', 'g', 'mg', 'mcg', 'IU'"
                        }
                    },
                    "required": ["name", "value", "units"]
                }
            },
            "ingredients": {
                "type": "array",
                "description": "A list of ingredients, if the item is a packaged food, medication or supplement. Empty if not applicable.",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["id", "nutrients", "ingredients"]
    }
}
prompt = (
    "You are an expert food scientist and nutritionist. Your job is to analyze the following list of metrics, identify only the items that are food, nutritional supplements or medications, and ignore all non-food/non supplement/no medications items (like \"Distance run\" or \"Apple stock price\")."
    "For each food, medication or supplement item you identify, you must:"
    "Use your internal knowledge to provide a comprehensive nutritional breakdown, including calories, macronutrients, fats, carbohydrates, protein, vitamins, fatty acids and minerals."
    "List its  ingredients if it is a packaged food, medication or supplement."
    "Your output must be ONLY a JSON array that strictly adheres to the provided schema. Match each output object to its original \"id\". If no food, medication or supplement items are found, output an empty array []."
    "Input Format: The input you will receive is a JSON array of objects, each with an \"id\" and a \"name\"."

    f"JSON Schema: \n {json.dumps(output_schema, indent=3)}"
    "**Data to Analyze**:\n"
)


def text_supplier(session: Session, message_input: MessageInput):
    if not message_input.note_id and not message_input.data_id:
        return None
    query = select(Data).join(Metric.data_points).where(and_(Data.note_id == note_id, Metric.tagged == False))

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


def on_response_from_model(session: Session, message_input: MessageInput, data: List[Dict[str, Any]]):
    if not message_input.note_id and not message_input.data_id:
        return
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
    process_record_factory(Params(tagging_prompt, text_supplier, Model(generative_model), max_tokens),
                           on_response_from_model))
