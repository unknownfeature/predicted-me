import json
import os
import traceback
from enum import Enum
from typing import Any, Dict, Callable, List

import boto3
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.lib import constants
from backend.lib.constants import name_is_required
from backend.lib.db import begin_session, Note
from backend.lib.util import call_bedrock_generative, text_getters, call_bedrock_embedding
from shared.variables import Env

sns_client = boto3.client('sns', region_name=os.getenv(Env.aws_region))
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)
max_tokens = os.getenv(Env.max_tokens)


#  this and the rest of it which uses this needs to be refactored todo
def handler_factory(process_record: Callable[[Dict[str, Any]], None]):
    def handler(event, _):
        for record in event[constants.records]:
            process_record(record)

    return handler

class BedrockModelType(str, Enum):
    generative = 'generative'
    embedding = 'embedding'


class Model:
    def __init__(self, name: str, type: BedrockModelType = BedrockModelType.generative):
        self.name = name
        self.type = type

class Params:

    def __init__(self, prompt: str, text_supplier: Callable[[Session, int, str], str], model: Model,
                 max_tokens: int = None):
        self.prompt = prompt
        self.text_supplier = text_supplier
        self.model = model
        self.max_tokens = max_tokens


def process_record_factory(params: Params, on_response_from_model: Callable[
    [Session, int, str, Dict[str, Any] | List[Dict[str, Any] | float]], None]) -> Callable[
    [Dict[str, Any]], None]:
    def process_record(record: Dict[str, Any]):
        session = begin_session()
        try:
            sns_notification = json.loads(record[constants.body])
            payload = json.loads(sns_notification[constants.message])
            note_id = payload.get(constants.note_id)
            origin = payload.get(constants.origin)

            if not note_id:
                print('Skipping record: note_id not found in payload.')
                return

            text = params.text_supplier(session, note_id, origin)

            if not text:
                print(f'Skipping record: text not found in payload {note_id}.')
                return
            data = None

            if params.model.type == BedrockModelType.generative:
                data = call_bedrock_generative(params.model.name, params.prompt, text,
                                                        max_tokens=params.max_tokens)
            elif params.model.type == BedrockModelType.embedding:
                data = call_bedrock_embedding(params.model.name, text)

            if not data:
                print(f'No numeric metrics extracted by Bedrock for Note ID {note_id}.')
                return

            on_response_from_model(session, note_id, origin, data)
        except Exception:
            session.rollback()
            traceback.print_exc()
            raise
        finally:
            session.close()

    return process_record


def note_text_supplier(session: Session, note_id: int, origin: str):
    note_query = select(Note).where(Note.id == note_id)
    target_note = session.scalar(note_query)

    if not target_note:
        return

    return text_getters[origin](target_note)
