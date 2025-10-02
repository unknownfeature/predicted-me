import json
import os
from typing import Any, Dict, List

import boto3
from sqlalchemy import insert, inspect
from sqlalchemy.orm import session

from backend.lib.db import Note, Link
from backend.lib.func.text_extraction import Function
from shared.variables import Env

sns_client = boto3.client('sns')
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)
max_tokens =  os.getenv(Env.max_tokens)

link_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": f"The full URL as it appears in the text. Max length: {inspect(Link).c.url.type.length} characters."
            },
            "description": {
                "type": "string",
                "description": f"A concise summary of the link's content based on the surrounding text. Max length: {inspect(Link).c.description.type.length} characters."
            },
        },
        "required": ["url", "description"]
    }
}

prompt = ("You are an expert at extracting links from text. Analyze the text below and extract all URLs starting with http or https. "
          "For each URL, derive a concise description from its surrounding context in the text. "
          "Your output must be ONLY a JSON array that strictly adheres to the provided schema. "
          "If no links are found, output an empty array [].\n\n"
          f"**JSON Schema**:\n{json.dumps(link_schema, indent=3)}\n\n"
          "**Text to Analyze**:\n")


def on_extracted_cb(sss: session, note_id: int, origin: str, data: List[Dict[str, Any]]) -> None:

    sss.execute((
        insert(Link.__table__)
        .values([d | {'note_id': note_id, 'origin': origin} for d in data])

        .on_conflict_do_nothing(
            index_elements=['ulr']
        )
    ))


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

