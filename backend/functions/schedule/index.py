import json
import traceback
from typing import Dict, Any, Union

from sqlalchemy import select, update, and_, delete as sql_delete
from sqlalchemy.orm import Session

from backend.lib.db import DataSchedule, begin_session, User
from backend.lib.util import get_user_id_from_event

updatable_fields = {'recurrence_schedule', 'target_value', 'units'}


def patch(session: Session, id: int, user_id: int, body: Dict[str, Any]) -> tuple[dict[str, Union[int, str]], int]:

    update_fields = {f: body[f] for f in body if f in updatable_fields}

    if update_fields:
        update_stmt = update(DataSchedule).join(DataSchedule.user).where(and_([DataSchedule.id == id, User.id == user_id])).values(**update_fields)
        session.execute(update_stmt)

    return {'status': 'success', 'schedule_id': id}, 200


def delete(session: Session, id: int, user_id: int) -> tuple[dict[str, Union[int, str]], int]:
      session.execute(sql_delete(DataSchedule).where( and_([DataSchedule.id == id, DataSchedule.user_id == user_id])))
      return {'status': 'success'}, 204


def post(session: Session, metric_id: int, user_id: int, body: Dict[str, Any]) -> Union[
    tuple[dict[str, str], int], tuple[dict[str, Union[str, Any]], int]]:
    schedule_exists = session.execute(select(DataSchedule).join(DataSchedule.user).where(and_([DataSchedule.metric_id == metric_id, User.id == user_id]))).first()

    if schedule_exists:
        return {'status': 'error', 'message': f'Schedule with id {metric_id} exists.'}, 403

    update_fields = {f: body[f] for f in body if f in {'recurrence_schedule', 'target_value', 'units'}} | {'metric_id': metric_id, 'user_id': user_id}
    schedule = DataSchedule(
        **update_fields)

    session.add(schedule)
    session.flush()


    return {'status': 'success', 'id': schedule.id}, 201


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = None

    try:

        session = begin_session()
        user_id = get_user_id_from_event(event, session)

        http_method = event['httpMethod']
        body = json.loads(event.get('body', '{}'))
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get("pathParameters", {})


        if http_method == 'PATCH':
            id = path_params['id']
            response_data, status_code = patch(session, id, user_id, body)
        elif http_method == 'POST' :
            metric_id  = query_params['metric_id']
            response_data, status_code = post(session, metric_id, user_id, body)
        elif http_method == 'DELETE':
            id = path_params['id']
            response_data, status_code = delete(session, id, user_id)
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