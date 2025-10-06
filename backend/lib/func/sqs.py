import os
import traceback
from typing import Any, Dict, Callable

import boto3
from sqlalchemy.orm import Session

from backend.lib.db import begin_session
from shared.variables import Env

sns_client = boto3.client('sns', region_name=os.getenv(Env.aws_region))
tagging_topic_arn = os.getenv(Env.tagging_topic_arn)

text_extraction_model = os.getenv(Env.generative_model)
max_tokens = os.getenv(Env.max_tokens)

def handler_factory(process_record: Callable[[Session, Dict[str, Any]], None]):
    def handler(event, _):
        session = None
        try:
            session = begin_session()

            for record in event['Records']:
                process_record(session, record)

            session.commit()
        except Exception as e:
            session.rollback()
            traceback.print_exc()
            raise e
        finally:
            if session:
                session.close()

    return handler

