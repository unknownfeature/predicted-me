from typing import Dict, Any, List

from sqlalchemy import select, update, and_, delete as sql_delete
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Data, Metric, Note, Tag, User, get_utc_timestamp_int
from backend.lib.func.http import handler_factory, RequestContext, delete_factory, patch_factory, post_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod

updatable_fileds = {'value', 'units', 'time'}


def post(session: Session, user_id, request_context: RequestContext) -> tuple[Dict[str, Any], int]:
    path_params = request_context.path_params
    body = request_context.body
    #  todo fix this, need to add another route to api
    metric_id = path_params['id']

    update_fields = {f: body[f] for f in body if f in updatable_fileds} | {
        'metric_id': metric_id, 'user_id': user_id, 'time': get_utc_timestamp_int()}
    data = Data(**update_fields)

    session.add(data)
    session.flush()

    return {'status': 'success', 'id': data.id}, 201

def get(session: Session, request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params

    path_params = request_context.path_params

    data_id = path_params.get('id')
    note_id = query_params.get('note_id')

    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    metrics = query_params.get('metrics').split(',') if 'metrics' in query_params else []
    end_time, start_time = get_ts_start_and_end(query_params)

    conditions = [
        Data.note.user_id == request_context.user.id
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

post_handler = lambda context: Data(**{f: context.body[f] for f in context.body if f in updatable_fileds} | {
        'metric_id': context.path_params['id'], 'user_id': context.user.id, 'time': get_utc_timestamp_int()})

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
    HttpMethod.PATCH.value: patch_factory(updatable_fileds, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})