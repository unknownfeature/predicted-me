import json
import os
from typing import Any, Dict, List

import boto3
from sqlalchemy import insert, inspect
from sqlalchemy.orm import Session

from backend.lib.db import Link
from backend.lib.func.sqs import handler_factory
from backend.lib.func.tagging import process_record_factory, Params
from backend.lib.func.text import note_text_supplier
from shared.variables import Env

sns_client = boto3.client('sns')
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

generative_model = os.getenv(Env.generative_model)
max_tokens =  int(os.getenv(Env.max_tokens))

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


prompt = (
    "You are an expert at extracting links from text. Analyze the text below and extract all web links (http/https). "
    "For each link, derive a concise description from its anchor text or surrounding context. "
    "Your output must be ONLY a JSON array that strictly adheres to the provided schema. "
    "If no links are found, output an empty array [].\n\n"
    f"**JSON Schema**:\n{json.dumps(link_schema, indent=3)}\n\n"
    "--- EXAMPLES ---\n"
    "Text: 'I've been learning a lot about AI. This article was helpful: https://ml-articles.com/intro. It covers the basics.'\n"
    "Output: [{\"url\": \"https://ml-articles.com/intro\", \"description\": \"An article about AI that covers the basics.\"}]\n\n"
    "Text: 'You can find our privacy policy at https://site.com/privacy and our terms of service are here: https://site.com/terms.'\n"
    "Output: [{\"url\": \"https://site.com/privacy\", \"description\": \"privacy policy\"}, {\"url\": \"https://site.com/terms\", \"description\": \"terms of service\"}]\n"
    "--- END EXAMPLES ---\n\n"
    "**Text to Analyze**:\n"
)


def on_extracted_cb(session: Session, note_id: int, origin: str, data: List[Dict[str, Any]]) -> None:

    session.execute((
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


handler = handler_factory(
    process_record_factory(Params(prompt, note_text_supplier, generative_model, max_tokens), on_extracted_cb))

