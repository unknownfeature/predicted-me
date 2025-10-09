import json
import os
from typing import List, Any, Dict

import boto3
from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import Task, Note, normalize_identifier, Origin
from backend.lib.func.sqs import handler_factory
from backend.lib.func.tagging import process_record_factory, Params
from backend.lib.func.text import note_text_supplier
from backend.lib.util import get_or_create_tasks
from shared.variables import Env

sns_client = boto3.client(constants.sns)
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

generative_model = os.getenv(Env.generative_model)
max_tokens =  int(os.getenv(Env.max_tokens))

task_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": f"A short and unique summary of the task. Max length: {inspect(Task).c.display_summary.type.length} characters."
            },
            "description": {
                "type": "string",
                "description": f"The full text of the task to be completed. Max length: {inspect(Task).c.description.type.length} characters."
            },
            "priority": {
                "type": "integer",
                "description": "An estimated priority from 1 (lowest) to 10 (highest). Default to 5 if not specified.",
                "minimum": 1,
                "maximum": 10
            }
        },
        "required": ["description", "priority"]
    }
}

prompt = ("You are an expert at identifying actionable tasks from text. Analyze the text below and extract all tasks. "
          "A task can be an item in a to-do list, a statement of intent (e.g., 'I need to...', 'remind me to...'), or an explicit command (e.g., 'add task:'). "
          "For each task, assign a priority from 1 (least important) to 10 (most important). If priority is not mentioned, use a default of 5. "
          "Your output must be ONLY a JSON array that strictly adheres to the provided schema. "
          "If no tasks are found, output an empty array []. "
          "Ignore metrics and links.\n\n"
          f"**JSON Schema**:\n{json.dumps(task_schema, indent=3)}\n\n"
          "--- EXAMPLES ---\n"
          "Text: 'My to-do list for tomorrow: 1. Finish the report that I've been working for a while. 2. Call the client who called me 2 days agoback. Also, I really have to schedule that dentist appointment, it's critical.'\n"
          "Output: [{\"summary\": \"Finish the report\", \"description\": \"More details on the report which is needed to be finished\", \"priority\": 5}, {\"summary\": \"Call the client back\", \"priority\": 5}, { \"description\": \"More details on dentist appointment if possible to extarct from the context\", \"summary\": \"schedule that dentist appointment\", \"priority\": 9}]\n\n"
          "Text: 'add task: buy milk, priority high'\n"
          "Output: [{\"summary\": \"buy milk\", \"priority\": 8, \"description\": \"detailed description of buyng milk if possible to extract otherwise the same as summary\"}]\n"
          "--- END EXAMPLES ---\n\n"
          "**Text to Analyze**:\n")

def on_extracted_cb(session: Session, note_id: int, origin: str, data: List[Dict[str, Any]]) -> None:
    note = session.query(Note).filter(Note.id == note_id).first()
    if not note:
        print(f"Note {note_id} not found")
        return
    existing = [l.summary for l in session.scalars(
        select(Task).where(and_(Task.url.in_([d[constants.url] for d in data]), Task.user_id == note.user_id))).unique()]

    new_ones = [Task(origin=Origin(origin),
                     url=l[constants.url],
                     user=note.user,
                     note=note,
                     summary=normalize_identifier(l[constants.summary]),
                     display_summary=l[constants.summary],
                     description=l[constants.description]) for l in data if l[constants.url] not in existing]
    if new_ones:
        session.add_all(new_ones)

    send_to_sns(note_id)


def send_to_sns(note_id):
    sns_client.publish(
        TopicArn=tagging_topic_arn,
        Note=json.dumps({
            constants.note_id: note_id,
        }),
        Subject='Extracted tasks ready for tagging'
    )


handler = handler_factory(
    process_record_factory(Params(prompt, note_text_supplier, generative_model, max_tokens), on_extracted_cb))
