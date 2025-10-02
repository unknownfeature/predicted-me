import json
import os
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import session

from backend.lib.func.tagging import Function
from shared.variables import Env

generative_model = os.getenv(Env.generative_model)
max_tokens =  os.getenv(Env.max_tokens)

tagging_prompt = """
You are an expert taxonomy and categorization engine. Analyze the provided metrics data (name, value, units, origin) 
and assign 1 to 3 relevant categories from the following global taxonomy: 
[HEALTH_FITNESS, NUTRITION, SOCIAL_MEDIA, FINANCIAL_WELLBEING, RECURRENT_GOAL, EMOTIONAL_STATE, ACTIVITY].

Output ONLY a JSON array where each object contains the original 'id' of the metric and a list of 'tags' assigned.
"""

def text_supplier(sss: session, note_id, _):
    query = select(Task).where(and_([Task.note_id == note_id, not Task.tagged]))

    untagged_tasks = sss.scalars(query).all()

    if not untagged_tasks:
        print(f"No tasks to tag{note_id} are already tagged. Skipping.")
        return

    return (
        f"\n{json.dumps([{
            'id': m.id,
            'description': m.name} for m in untagged_tasks
        ])}"
    )



def on_extracted_cb(sss: session, note_id: int, tags: List[Dict[str, Any]]):
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