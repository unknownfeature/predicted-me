import json
import os
import traceback
from typing import List, Dict, Any

from sqlalchemy import select, or_, inspect
from sqlalchemy.orm import Session

from backend.lib.db import begin_session, Metric, to_func_enum
from backend.lib import util
from shared import constants
from shared.constants import default_max_tokens
from shared.variables import *

generative_model = os.getenv(generative_model)
max_tokens = int(os.getenv(max_tokens,  default_max_tokens))
batch_size = int(os.getenv(batch_size,  default_max_tokens))


schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {
                "type": "number",
                "description": "The original ID of the metric being analyzed."
            },
            "default_units": {
                "type": "string",
                "description": f"The most common standard unit for this metric (e.g., 'lbs', 'miles', 'kcal', 'mg'). Use 'count' for simple counters. Use null if not applicable. Max length: {inspect(Metric).c.default_units.type.length} characters."
            },
            "default_aggregator_function": {
                "type": "string",
                "description": f"The most logical default aggregation function for this metric.   Max length: {inspect(Metric).c.default_aggregator_function.type.length} characters.",
                "enum": ["sum", "avg", "min", "max", "last", "median", "count", "none"]
            },
            "default_aggregation_period_seconds": {
                "type": "number",
                "description": "The most common period in seconds for this metric (e.g., 86400 for daily, 3600 for hourly). Use null if not applicable."
            }
        },
        "required": ["id", "default_units", "default_aggregator_function", "default_aggregation_period_seconds"]
    }
}

prompt = (
    "You are an expert data architect. Your job is to analyze a list of metric names and assign default aggregation properties to them. "
    "Your output must be ONLY a JSON array that strictly adheres to the provided schema. Return null for fields that do not apply.\n\n"
    f"**JSON Schema**:\n{json.dumps(schema, indent=3)}\n\n"
    "--- EXAMPLES ---\n"
    "Input:\n"
    '[{"id": 1, "name": "Distance Run"}, {"id": 2, "name": "Weight"}, {"id": 3, "name": "Vitamin D"}]\n'
    "Output:\n"
    '[\n'
    '  {"id": 1, "default_units": "miles", "default_aggregator_function": "sum", "default_aggregation_period_seconds": 86400},\n'
    '  {"id": 2, "default_units": "lbs", "default_aggregator_function": "last", "default_aggregation_period_seconds": 86400},\n'
    '  {"id": 3, "default_units": "mcg", "default_aggregator_function": "sum", "default_aggregation_period_seconds": 86400}\n'
    ']\n'
    "--- END EXAMPLES ---\n\n"
    "**Metrics to Analyze**:\n"
)





def update_metrics_in_db(session: Session, metrics_data: List[Dict[str, Any]]):
    metrics_map = {metric.id: metric for metric in session.scalars(
        select(Metric).where(Metric.id.in_([m[constants.id] for m in metrics_data]))
    ).unique()}

    for item in metrics_data:
        metric_to_update = metrics_map.get(item['id'])
        if not metric_to_update:
            continue

        agg_func = to_func_enum(item.get(constants.default_aggregator_function))
        units = item.get(constants.default_units)
        period = item.get(constants.default_aggregation_period_seconds)

        if metric_to_update.default_aggregator_function is None:
            metric_to_update.default_aggregator_function = agg_func

        if metric_to_update.default_units is None:
            metric_to_update.default_units = units

        if metric_to_update.default_aggregation_period_seconds is None:
            metric_to_update.default_aggregation_period_seconds = period

        session.add(metric_to_update)
    session.commit()




def handler(_, __):
    print("Starting metric defaults population job...")
    session = begin_session()

    try:
        page = 0
        while True:
            print(f"Processing page {page}...")

            query = (
                select(Metric)
                .where(or_(
                    *[Metric.default_aggregator_function.is_(None),
                    Metric.default_units.is_(None),
                    Metric.default_aggregation_period_seconds.is_(None)]
                ))
                .order_by(Metric.id)
                .limit(batch_size)
                .offset(page * batch_size)
            )

            metrics_batch = session.scalars(query).unique()

            if not metrics_batch:
                print("No more metrics to process. Job complete.")
                break

            llm_input = [
                {constants.id: m.id, constants.name: m.display_name}
                for m in metrics_batch
            ]

            if not llm_input:
                print("No more metrics to process. Job complete.")
                break

            llm_response = call_generative(generative_model, prompt, json.dumps(llm_input),  max_tokens)

            if not llm_response:
                print("Received empty response from LLM. Stopping.")
                break

            update_metrics_in_db(session, llm_response)

            page += 1

    except Exception as e:

        session.rollback()
        traceback.print_exc()
    finally:
        session.close()

def call_generative(model: str, prompt: str, text_content: str, max_tokens: int = 3072) -> List[Dict[str, Any]]:
    return util.call_generative(model, prompt, text_content, max_tokens)