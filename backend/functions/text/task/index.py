import json
import os
from typing import List, Any, Dict

import boto3
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from shared import constants
from backend.lib.db import Task, Note, normalize_identifier, Origin, Occurrence
from backend.lib.func.sqs import handler_factory, Model
from backend.lib.func.sqs import process_record_factory, Params, note_text_supplier
from backend.lib.util import get_or_create_tasks
from shared.variables import *

sns_client = boto3.client(constants.sns)
tagging_topic_arn = os.getenv(tagging_topic_arn)

generative_model = os.getenv(generative_model)
max_tokens =  int(os.getenv(max_tokens))

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
        "required": ["description", "priority", "summary"]
    }
}

prompt = ("You are an expert at identifying actionable tasks from text. Analyze the text below and extract all tasks. "
          "A task can be an item in a to-do list, a statement of intent (e.g., 'I need to...', 'remind me to...'), or an explicit command (e.g., 'add task:'). "
          "For each task, assign a priority from 1 (least important) to 10 (most important). If priority is not mentioned, use a default of 5. "
          "Your output must be ONLY a JSON array that strictly adheres to the provided db. "
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

def on_response_from_model(session: Session, note_id: int, data: List[Dict[str, Any]]) -> None:
    target_note = session.scalar(select(Note).where(Note.id == note_id))
    tasks_map = get_or_create_tasks(session, {
        normalize_identifier(item[constants.summary]): {constants.summary: item[constants.summary],
                                                        constants.description: item[constants.description]} for item in
        data}, target_note.user_id)
    occurrence_to_add = [
        Occurrence(priority=d.get(constants.priority),
             task=tasks_map[normalize_identifier(d.get(constants.summary))],
             note=target_note)
     for d in data if constants.summary in d]


    if  occurrence_to_add:
        session.add_all(occurrence_to_add)
        session.commit()
        send_to_sns(target_note.id)



def send_to_sns(note_id):
    sns_client.publish(
        TopicArn=tagging_topic_arn,
        Note=json.dumps({
            constants.note_id: note_id,
        }),
        Subject='Extracted tasks ready for tagging'
    )


handler = handler_factory(
    process_record_factory(Params(prompt, note_text_supplier, Model(generative_model), max_tokens), on_response_from_model))
