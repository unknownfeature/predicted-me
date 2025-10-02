import json
import traceback
from typing import Dict, Any, List, Union

from sqlalchemy import select, update, and_, delete as sql_delete
from sqlalchemy.orm import session, joinedload

from backend.lib.db import Data, Metrics, begin_session, Note, DataSchedule, Tag, User
from backend.lib.util import get_user_id_from_event, get_ts_start_and_end


def delete(session: session, id: int, user_id: int) -> tuple[dict[str, Union[int, str]], int]:
    session.execute(sql_delete(Data).where(
        and_(
            Data.id == id,
            Data.note.has(Note.user_id == user_id)
        )
    )
    )
    return {'status': 'success'}, 204


def get(session: session, user_id: int, query_params: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
    data_id = query_params.get('id')
    note_id = query_params.get('note_id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    metrics = query_params.get('metrics').split(',') if 'metrics' in query_params else []
    end_time, start_time = get_ts_start_and_end(query_params)
    conditions = [
        Data.note.user_id == user_id
    ]
    query = select(Data).join(Data.note)

    if not note_id and not data_id:
        conditions.extend([
            Data.time >= start_time,
            Data.time <= end_time
        ])
        if tags or metrics:
            query = query.join(Data.metric)
        if tags:
            conditions.append(Metrics.tags.any(Tag.tag.in_(tags)))
        if metrics:
            conditions.append(Metrics.name.in_(metrics))
    elif data_id:
        conditions.append(Data.id == int(data_id))
    elif note_id:
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Note.time.desc()) \
        .options(
        joinedload(Data.metric).joinedload(Metrics.tags),
        joinedload(Data.metric).joinedload(Metrics.schedules)
    )

    data_points = session.scalars(query).all()

    return [{
        'id': dp.id,
        'note_id': dp.note_id,
        'value': float(dp.value),
        'units': dp.units,
        'origin': dp.origin.value,
        'metric': {
            'id': dp.metric.id,
            'name': dp.metric.name,
            'is_tagged': dp.metric.tagged,
            'tags': [tag for tag in dp.metric.tags],
            'schedule': {} if dp.metric.schedules is None else {
                'id': dp.metric.schedules[0].id,
                'recurrence_schedule': dp.metric.schedules[0].recurrence_schedule,
                'target_value': dp.metric.schedules[0].target_value,
                'units': dp.metric.schedules[0].units,
            }
        }} for dp in data_points], 200


def patch(session: session, id: int, user_id, body: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    update_fields = {f: body[f] for f in body if f in {'value', 'units', 'time'}}

    if update_fields:
        update_stmt = update(Data).join(Data.note).where(and_([Data.id == id, User.id == user_id])).values(
            **update_fields)
        session.execute(update_stmt)

    return {'status': 'success', 'data_id': id}, 200


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
            response_data, status_code = get(session, user_id, query_params)

        elif http_method == 'PATCH':
            id = path_params['id']
            response_data, status_code = patch(session, id, user_id, body)
            session.commit()

        elif http_method == 'DELETE':
            id = path_params['id']
            response_data, status_code = delete(session, id, user_id)
            session.commit()

        else:
            return {'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'})}

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
