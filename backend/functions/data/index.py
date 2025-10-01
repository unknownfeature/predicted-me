import json
import traceback
from typing import Dict, Any, List

from sqlalchemy import select, update, and_
from sqlalchemy.orm import session, joinedload

from backend.lib.db import Data, Metrics, begin_session, Note, DataSchedule
from backend.lib.util import get_user_id_from_event, get_ts_start_and_end


def get(session: session, user_id: int, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    conditions = [
        Data.note.user_id == user_id
    ]

    data_id = query_params.get('id')
    note_id = query_params.get('note_id')
    end_time, start_time = get_ts_start_and_end(query_params)

    if not note_id and not data_id:
        conditions.append(Data.time >= start_time)
        conditions.append(Data.time <= end_time)
    elif data_id:
        conditions.append(Data.id == int(data_id))
    elif note_id:
        conditions.append(Data.note.id == int(note_id))

    query = select(Data).join(Note).options(joinedload(Data.metric_type).joinedload(Metrics.tags).joinedload(
        Metrics.schedules)).filter(DataSchedule.user_id == user_id).where(and_(*conditions))

    data_points = session.scalars(query).all()

    return [{
        'id': dp.id,
        'message_id': dp.message_id,
        'value': float(dp.value),
        'units': dp.units,
        'origin': dp.origin.value,
        'metric': {
            'id': dp.metric_type.id,
            'name': dp.metric_type.name,
            'is_tagged': dp.metric_type.tagged,
            'tags': [tag for tag in dp.metric_type.tags],
            'schedule': {} if dp.metric_type.schedules is None else {
                'recurrence_schedule': dp.metric_type.schedules[0].recurrence_schedule,
                'target_value': dp.metric_type.schedules[0].target_value,
                'units': dp.metric_type.schedules[0].units,
            }
        }} for dp in data_points]


def patch(session: session, id: int, body: Dict[str, Any]) -> Dict[str, Any]:
    target_data = session.get(Data, id)
    if not target_data:
        raise ValueError(f"Data point ID {id} not found.")

    update_fields = {f for f in body if f in {'value', 'units', 'time'}}

    if update_fields:
        update_stmt = update(Data).where(Data.id == id).values(**update_fields)
        session.execute(update_stmt)

    return {'status': 'success', 'data_id': id}


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:

        session = begin_session()
        user_id = get_user_id_from_event(event, session)

        http_method = event['httpMethod']
        body = json.loads(event.get('body', '{}'))
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get("pathParameters", {})

        if http_method == 'GET':
            response_data = get(session, user_id, query_params)
            status_code = 200

        elif http_method == 'PATCH':
            data_id = path_params['id']
            response_data = patch(session, int(data_id), body)
            status_code = 200

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'})}

        session.commit()

        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }


    except Exception:
        if session:
            session.rollback()
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}

    finally:
        if session:
            session.close()
