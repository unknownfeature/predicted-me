import json
import os
import traceback
from enum import Enum
from typing import Any, Dict, Callable, List, Optional

import boto3
from sqlalchemy.orm import Session
from sqlalchemy import select

from shared import constants
from backend.lib.db import begin_session, Note, Origin
from backend.lib.util import call_bedrock_generative, text_getters, call_bedrock_embedding
from shared.variables import *

sns_client = boto3.client('sns', region_name=os.getenv(aws_region))
tagging_topic_arn = os.getenv(tagging_topic_arn)

text_extraction_model = os.getenv(generative_model)
max_tokens = os.getenv(max_tokens)


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

            on_response_from_model(session, note_id, data)
        except Exception:
            session.rollback()
            traceback.print_exc()
            raise
        finally:
            session.close()

    return process_record

#  refactor and test todo
def note_text_supplier(session: Session, note_id: int, origin: str) -> Optional[str]:
    note_query = select(Note).where(Note.id == note_id)
    target_note = session.scalar(note_query)

    if not target_note:
        return None

    if origin == Origin.text.value:
        if target_note.image_key is None:
            return target_note.text
        if target_note.image_described:
            return f'{target_note.text}. Image description: {target_note.image_description}. Image text: {target_note.image_text}'

    elif origin == Origin.audio_text.value and target_note.audio_transcribed:
        if target_note.image_key is None:
            return target_note.audio_text

        if target_note.image_described:
            return f'{target_note.audio_text}. Image description: {target_note.image_description}. Image text: {target_note.image_text}'
    elif target_note.image_described:
        # origin can only be image here
       if target_note.text:
           return f'{target_note.text}. Image description: {target_note.image_description}. Image text: {target_note.image_text}'

       if target_note.audio_key and target_note.audio_transcribed:
               return f'{target_note.audio_text}. Image description: {target_note.image_description}. Image text: {target_note.image_text}'
       elif not target_note.audio_key:
           return f'Image description: {target_note.image_description}. Image text: {target_note.image_text}'


