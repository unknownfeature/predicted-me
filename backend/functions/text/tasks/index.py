import json
import os
from typing import List, Any, Dict

import boto3
from sqlalchemy import insert, inspect
from sqlalchemy.orm import session

from backend.lib.db import Note, Task
from backend.lib.func.text_extraction import Function
from shared.variables import Env

sns_client = boto3.client('sns')
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)
max_tokens =  os.getenv(Env.max_tokens)

task_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
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
          "Text: 'My to-do list for tomorrow: 1. Finish the report. 2. Call the client back. Also, I really have to schedule that dentist appointment, it's critical.'\n"
          "Output: [{\"description\": \"Finish the report\", \"priority\": 5}, {\"description\": \"Call the client back\", \"priority\": 5}, {\"description\": \"schedule that dentist appointment\", \"priority\": 9}]\n\n"
          "Text: 'add task: buy milk, priority high'\n"
          "Output: [{\"description\": \"buy milk\", \"priority\": 8}]\n"
          "--- END EXAMPLES ---\n\n"
          "**Text to Analyze**:\n")

def on_extracted_cb(sss: session , note_id: int, origin: str, data: List[Dict[str, Any]]) -> None:


    sss.execute(insert(Task.__table__)
                    .values([d | {'note_id': note_id, 'origin': origin} for d in data ]))

    sns_client.publish(
        TopicArn=tagging_topic_arn,
        Note=json.dumps({
            'note_id': note_id,
        }),
        Subject='Extracted tasks ready for tagging'
    )

text_processing_function = Function(prompt, on_extracted_cb, text_extraction_model, int(max_tokens))


def handler(event, _):
    return text_processing_function.handler(event, None)

