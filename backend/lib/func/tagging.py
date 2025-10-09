import json
from typing import Callable, Dict, Any, List
from sqlalchemy.orm import Session

from backend.lib.util import call_bedrock


class Params:

    def __init__(self, prompt: str, text_supplier: Callable[[Session, int, str], str], generative_model: str,
                 max_tokens: int):
        self.prompt = prompt
        self.text_supplier = text_supplier
        self.generative_model = generative_model
        self.max_tokens = max_tokens


def process_record_factory(params: Params, on_extracted_cb: Callable[
    [Session, int, str, Dict[str, Any] | List[Dict[str, Any]]], None]) -> Callable[[Session, Dict[str, Any]], None]:


    def process_record(session: Session, record: Dict[str, Any]):

        sns_notification = json.loads(record['body'])
        payload = json.loads(sns_notification['Message'])
        note_id = payload.get('note_id')
        origin = payload.get('origin')

        if not note_id:
            print("Skipping record: note_id not found in payload.")
            return

        text = params.text_supplier(session, note_id, origin)

        if not text:
            print(f"Skipping record: text not found in payload {note_id}.")
            return

        extracted_metrics = call_bedrock(params.generative_model, params.prompt, text,
                                         max_tokens=params.max_tokens)

        if not extracted_metrics:
            print(f"No numeric metrics extracted by Bedrock for Note ID {note_id}.")
            return

        on_extracted_cb(session, note_id, origin, extracted_metrics)

        session.commit()

    return process_record
