import os
import unittest
import uuid
from enum import Enum
from typing import Dict, Any

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.lib.db import Base, User, Metric
from shared.variables import Env

load_dotenv()
connection_str = f'mysql+mysqlconnector://{os.getenv(Env.db_user)}:{os.getenv(Env.db_pass)}@{os.getenv(Env.db_endpoint)}:3306/{os.getenv(Env.db_name)}'


def prepare_http_event(external_user_id: str) -> Dict[str, Any]:
    return {
        'body': {},
        'queryStringParameters': {},
        'pathParameters': {},
        'requestContext': {'authorizer': {'jwt': {'claims': {'username': external_user_id}}}},

    }

def get_metrics_by_name(name, session):
    return session.query(Metric).filter(Metric.name == name).all()

def get_metrics_by_display_name(display_name, session):
    return session.query(Metric).filter(Metric.display_name == display_name).all()

class Trigger(str, Enum):
    http = 'http'
    sqs = 'sqs'


def baseSetUp(trigger: Trigger) -> Dict[str, Any]:
    engine = create_engine(connection_str, echo=True)
    session = sessionmaker(bind=engine, autoflush=True)()
    external_id = uuid.uuid4().hex

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session.add(User(external_id=external_id))
    session.flush()
    other_external_id = uuid.uuid4().hex
    session.add(User(external_id=other_external_id))
    session.commit()
    session.close()
    if trigger == Trigger.http:
        return prepare_http_event(external_id)


def baseTearDown():
    engine = create_engine(connection_str)
    Base.metadata.drop_all(engine)
