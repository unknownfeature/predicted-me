from  datetime import datetime, timezone
import json
import os

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.variables import Env


def get_user_id_from_external_id(session: session, external_id: str) -> int:
    user_query = select(User.id).where(User.external_id == external_id)
    return session.scalar(user_query)


def get_utc_timestamp_int() -> int:
    return int(datetime.now(timezone.utc).timestamp())