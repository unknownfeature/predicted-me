import json
import os
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, Callable, List

import boto3
from sqlalchemy.orm import session

from backend.lib.db import begin_session
from backend.lib.util import call_bedrock
from shared.variables import Env

sns_client = boto3.client('sns')
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)
max_tokens = os.getenv(Env.max_tokens)


class AbstractSQSTriggeredFunction(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def process_record(self, session: Session, record: Dict[str, Any]):
        pass

    def handler(self, event, _):
        session = None
        try:
            session = begin_session()

            for record in event['Records']:
                self.process_record(session, record)
            session.commit()
        except Exception as e:
            session.rollback()
            traceback.print_exc()
            raise e
        finally:
            if session:
                session.close()

        return {'statusCode': 200, 'body': f"Successfully processed {len(event['Records'])} SQS notes."}


class BaseSQSTriggeredLLMClientFunction(AbstractSQSTriggeredFunction):
    def __init__(self, prompt: str, text_supplier: Callable[[session, int, str], str],
                 on_extracted_cb: Callable[[session, int, str, List[Dict[str, Any]]], None],
                 generative_model: str, max_tokens: int):
        super().__init__()
        self.prompt = prompt
        self.text_supplier = text_supplier
        self.on_extracted_cb = on_extracted_cb
        self.generative_model = generative_model
        self.max_tokens = max_tokens

    def process_record(self, session: Session, record: Dict[str, Any]):

        sns_notification = json.loads(record['body'])
        payload = json.loads(sns_notification['Note'])
        note_id = payload.get('note_id')
        origin = payload.get('origin')

        if not note_id:
            print("Skipping record: note_id not found in payload.")
            return

        text = self.text_supplier(session, note_id, origin)

        if not text:
            print(f"Skipping record: text not found in payload {note_id}.")
            return

        extracted_metrics = call_bedrock(self.generative_model, self.prompt, text,
                                         max_tokens=self.max_tokens)

        if not extracted_metrics:
            print(f"No numeric metrics extracted by Bedrock for Note ID {note_id}.")
            return
        self.on_extracted_cb(session, note_id, origin, extracted_metrics)
