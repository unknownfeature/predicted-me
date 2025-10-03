from typing import Dict, Any, List

from sqlalchemy import select, update, and_, delete as sql_delete
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Data, Metric, Note, Tag, User
from backend.lib.func.http import handler_factory, RequestContext, delete_factory, patch_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod


def get(session: Session, user_id: int, request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params

    path_params = request_context.path_params

    data_id = path_params.get('id')
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
            conditions.append(Metric.tags.any(Tag.name.in_(tags)))
        if metrics:
            conditions.append(Metric.name.in_(metrics))
    elif data_id:
        conditions.append(Data.id == int(data_id))
    elif note_id:
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Data.time.desc()) \
        .options(
        joinedload(Data.metric).joinedload(Metric.tags),
        joinedload(Data.metric).joinedload(Metric.schedules)
    )

    data_points = session.scalars(query).all()

    return [{
        'id': dp.id,
        'note_id': dp.note_id,
        'value': float(dp.value),
        'units': dp.units,
        'origin': dp.origin.value,
        'time': dp.time,
        'metric': {
            'id': dp.metric.id,
            'name': dp.metric.name,
            'tagged': dp.metric.tagged,
            'tags': [tag for tag in dp.metric.tags],
            'schedule': {} if dp.metric.schedules is None else {
                'id': dp.metric.schedules[0].id,
                'recurrence_schedule': dp.metric.schedules[0].recurrence_schedule,
                'target_value': dp.metric.schedules[0].target_value,
                'units': dp.metric.schedules[0].units,
            }
        }} for dp in data_points], 200


patch_handler = lambda session, update_fields, user_id, id: session.execute(update(Data).where(
                                                     and_([Data.id == id, User.id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(sql_delete(Data).where(
                                                     and_([Data.id == id, Data.note.has(Note.user_id == user_id)])))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch_factory({'value', 'units', 'time'}, patch_handler
                                          ),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})