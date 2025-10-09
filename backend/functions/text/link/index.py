import json
import os
from typing import Any, Dict, List

import boto3
from sqlalchemy import inspect, select, and_
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import Link, normalize_identifier, Note, Origin
from backend.lib.func.sqs import handler_factory
from backend.lib.func.tagging import process_record_factory, Params
from backend.lib.func.text import note_text_supplier
from shared.variables import Env

sns_client = boto3.client(constants.sns, region_name=os.getenv(Env.aws_region))
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

generative_model = os.getenv(Env.generative_model)
max_tokens = int(os.getenv(Env.max_tokens))

link_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": f"The full URL as it appears in the text. Max length: {inspect(Link).c.url.type.length} characters."
            },
            "summary": {
                "type": "string",
                "description": f"A brief summary of the link's description. Max length: {inspect(Link).c.display_summary.type.length} characters."
            },
            "description": {
                "type": "string",
                "description": f"A concise description of the link's content based on the surrounding text. Max length: {inspect(Link).c.description.type.length} characters."
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
    "Text: constants.Ive been learning a lot about AI. This article was helpful: https://ml-articles.com/intro. It covers the basics.'\n"
    "Output: [{\"url\": \"https://ml-articles.com/intro\",\"summary\": \"An article about AI that covers the basics.\", \"description\": \"More detail.ed description of what exactly basics this article covers\"}]\n\n"
    "Text: 'You can find our privacy policy at https://site.com/privacy and our terms of service are here: https://site.com/terms.'\n"
    "Output: [{\"url\": \"https://site.com/privacy\", \"summary\": \"privacy policy\",  \"description\": \"More detailed description of privacy policy\"}, {\"url\": \"https://site.com/terms\", \"summary\": \"terms of service\", \"description\": \"More detailed description of terms of service\"}]\n"
    "--- END EXAMPLES ---\n\n"
    "**Text to Analyze**:\n"
)

# todo in some places I commit in CB and in some in the calling code
# here we need to make sure changes are in DB before sending the message so we need to commit here
def on_extracted_cb(session: Session, note_id: int, origin: str, data: List[Dict[str, Any]]) -> None:
    note = session.query(Note).filter(Note.id == note_id).first()
    if not note:
        print(f"Note {note_id} not found")
        return
    existing = [l.url for l in session.scalars(
        select(Link).where(and_(Link.url.in_([d[constants.url] for d in data]), Link.user_id == note.user_id))).unique()]

    new_ones = [Link(origin=Origin(origin),
                     url=l[constants.url],
                     user=note.user,
                     note=note,
                     summary=normalize_identifier(l[constants.summary]),
                     display_summary=l[constants.summary],
                     description=l[constants.description]) for l in data if l[constants.url] not in existing]
    if new_ones:
        session.add_all(new_ones)
        session.commit()

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
