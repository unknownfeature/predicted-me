from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import session

from backend.lib.db import User, get_utc_timestamp_int

seconds_in_day = 24 * 60 * 60

def get_user_id_from_event(event: Dict[str, Any], session: session) -> int:
    user_query = select(User.id).where(User.external_id == event['requestContext']['authorizer']['jwt']['claims']['username'])
    return session.scalar(user_query)

def get_ts_start_and_end(query_params):
    now_utc = get_utc_timestamp_int()
    start_time = int(query_params.get('start_ts')) if 'start_ts' in query_params else (now_utc - seconds_in_day)
    end_time = int(query_params.get('end_ts')) if 'end_ts' in query_params else now_utc
    if start_time >= end_time:
        raise ValueError("Start time must be before end time.")
    return start_time, end_time
