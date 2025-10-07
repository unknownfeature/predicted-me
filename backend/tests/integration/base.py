import os
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List, Type

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.lib.db import Base, User, Metric, Task, begin_session, normalize_identifier, get_utc_timestamp, Link, Note
from backend.lib import constants
from backend.lib.func.http import seconds_in_day
from shared.variables import Env

load_dotenv()
connection_str = f'mysql+mysqlconnector://{os.getenv(Env.db_user)}:{os.getenv(Env.db_pass)}@{os.getenv(Env.db_endpoint)}:3306/{os.getenv(Env.db_name)}'

legit_user_id = 1
malicious_user_id =  2

tag_one_display_name = 'tag one Test 4^'
tag_two_display_name = 'tag & two_ la la'
tag_three_display_name = 'tag ^ three ??'

tag_one_name = normalize_identifier(tag_one_display_name)
tag_two_name = normalize_identifier(tag_two_display_name)
tag_three_name = normalize_identifier(tag_three_display_name)

time_now = get_utc_timestamp()
day_ago = time_now - seconds_in_day
two_days_ago = time_now - seconds_in_day * 2
three_days_ago = time_now - seconds_in_day * 3

unique_piece = 'unique piece'


def prepare_http_event(external_user_id: str) -> Dict[str, Any]:
    return {
        constants.body: {},
        constants.query_params: {},
        constants.path_params: {},
        'requestContext': {'authorizer': {'jwt': {'claims': {'username': external_user_id}}}},

    }
def refresh_cache(session):
    session.close()
    session = begin_session()
    return session


def get_metric_by_id(metric_id: int, session: Session) -> Optional[Metric]:
    return session.query(Metric).filter(Metric.id == metric_id).first()

def get_metrics_by_name(name: str, session: Session) -> List[Type[Metric]]:
    return session.query(Metric).filter(Metric.name == name).all()

def get_metrics_by_display_name(display_name: str, session: Session) -> List[Type[Metric]]:
    return session.query(Metric).filter(Metric.display_name == display_name).all()

def get_task_by_id(task_id: int, session: Session) -> Optional[Task]:
    return session.query(Task).get(task_id)
def get_tasks_by_display_summary(display_summary: str, session: Session) -> List[Type[Task]]:
    return session.query(Task).filter(Task.display_summary == display_summary).all()

def get_tasks_by_summary(summary: str, session: Session) -> List[Type[Task]]:
    return session.query(Task).filter(Task.summary == summary).all()

def get_tasks_by_description(desc: str, session: Session) -> List[Type[Task]]:
    return session.query(Task).filter(Task.description == desc).all()

def get_links_by_description(desc: str, session: Session) -> List[Type[Link]]:
    return session.query(Link).filter(Link.description == desc).all()

def get_link_by_id(link_id: int, session: Session) -> Optional[Link]:
    return session.query(Link).filter(Link.id == link_id).first()

def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    return session.query(User).get(user_id)

def get_note_by_text(text: str, session: Session) -> Optional[Note]:
    return session.query(Note).get(text)

def get_notes_by_text(text: str, session: Session) -> List[Type[Note]]:
    return session.query(Note).filter(Note.text == text).all()

class Trigger(str, Enum):
    http = 'http'
    sqs = 'sqs'
    s3 = 's3'


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
