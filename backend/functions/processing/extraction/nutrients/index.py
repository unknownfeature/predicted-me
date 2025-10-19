import json
import os
from typing import List, Dict, Any

from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session, selectinload, joinedload

from shared import constants
from backend.lib.db import Metric, Data, Tag, Note, normalize_identifier
from backend.lib.func.sqs import process_record_factory, Params, handler_factory, Model, MessageInput
from backend.lib.util import add_tags, get_or_create_metrics
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
                "description": "The original 'id' of the food, medication or supplement item being analyzed."
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

    conditions = []
    if message_input.note_id:
        conditions.append(Data.note_id == message_input.note_id)
    if message_input.data_id:
        conditions.append(Data.id == message_input.data_id)
    conditions.append(Metric.tagged == False)

    query = select(Data).join(Data.metric).options(joinedload(Data.metric)).where(and_(*conditions))

    unprocessed_data = session.scalars(query).unique().all()

    if not unprocessed_data:
        return

    return json.dumps([{
        constants.id: d.id,
        constants.name: d.metric.display_name} for d in unprocessed_data
    ])


def get_user_id(session: Session, message_input: MessageInput):
    if message_input.note_id:
        note = session.get(Note, message_input.note_id)
        return note.user_id
    elif message_input.data_id:
        stmt = select(Metric).join(Metric.data_points).where(Data.id == message_input.data_id)
        metric = session.scalar(stmt)
        return metric.user_id

    else:
        raise ValueError('no metric id and no note id')  # should not happen

def get_or_create_tag(display_name: str, session: Session, user_id: int):
    normalized_name = normalize_identifier(display_name)
    existing = session.scalars(select(Tag).where(
        and_(Tag.user_id == user_id, Tag.name == normalized_name))).first()
    if not existing:
        new_tag = Tag(name=normalized_name, user_id=user_id, display_name=display_name)
        session.add(new_tag)
        return new_tag
    return existing

def on_response_from_model(session: Session, message_input: MessageInput, data: List[Dict[str, Any]]):
    user_id = get_user_id(session, message_input)
    for data_item in data:
        data_id = data_item.get(constants.id)
        nutrients = data_item.get(constants.nutrients)
        ingredients = data_item.get(constants.ingredients)
        if nutrients:
            nutrient_tag = get_or_create_tag(constants.nutrient_tag, session, user_id)
            for nutrient in nutrients:
                process_nutrient(data_id, nutrient, nutrient_tag, session, user_id)
        if ingredients:
            ingredient_tag = get_or_create_tag(constants.ingredient_tag, session, user_id)
            for ingredient in ingredients:
                process_ingredient(data_id, ingredient, ingredient_tag, session, user_id)

    session.commit()


def process_ingredient(data_id: int, ingredient: str, ingredient_tag: Tag, session: Session, user_id: int):
    normalized_name = normalize_identifier(ingredient)
    ingredient_metric = get_or_create_metrics(session, {normalized_name: ingredient}, user_id)[normalized_name]
    if not ingredient_metric.tagged:
        ingredient_metric.tagged = True
        ingredient_metric.tags.append(ingredient_tag)
    ingredient_metric.data_points.append(Data(value=1, parent_data_id=data_id))


def process_nutrient(data_id: int, nutrient: Dict[str, Any], nutrient_tag: Tag, session: Session, user_id: int):
    name = nutrient[constants.name]
    value = nutrient[constants.value]
    units = nutrient[constants.units]
    normalized_name = normalize_identifier(name)
    nutrient_metric = get_or_create_metrics(session, {normalized_name: name}, user_id)[normalized_name]
    if not nutrient_metric.tagged:
        nutrient_metric.tagged = True
        nutrient_metric.tags.append(nutrient_tag)
    nutrient_metric.data_points.append(Data(value=value, units=units, parent_data_id=data_id))


handler = handler_factory(
    process_record_factory(Params(prompt, text_supplier, Model(generative_model), max_tokens),
                           on_response_from_model))
