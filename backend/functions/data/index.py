from typing import Dict, Any, List, Tuple

from sqlalchemy import select, update, and_, delete as sql_delete, or_, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Data, Metric, Note, Tag, Origin
from backend.lib.func import constants
from backend.lib.func.http import handler_factory, RequestContext, delete_factory, patch_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod

updatable_fileds = {constants.value, constants.units, constants.time}


def post(session: Session, request_context: RequestContext) -> Tuple[Dict[str, Any], int]:
    body = request_context.body
    id = request_context.path_params[constants.id]

    metric = session.scalars(
        select(Metric).where(and_(* [Metric.user_id == request_context.user.id, Metric.id == id]))).first()
    if not metric:
        return {constants.status: constants.not_found}, 404
    data = Data(**{f: body[f] for f in body if f in updatable_fileds} | {constants.origin: Origin.user.value},
                metric=metric)
    session.add(data)
    session.commit()
    return {constants.status: constants.success, constants.id: data.id}, 201


def get(session: Session, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params

    path_params = request_context.path_params

    data_id = path_params.get(constants.id)
    note_id = query_params.get(constants.note_id)

    tags = query_params.get(constants.tags).split(
        '|') if constants.tags in query_params else []  # todo display name still can have it but probably rare
    metric = query_params.get(constants.metric)
    start_time, end_time = get_ts_start_and_end(query_params)

    conditions = [
        Metric.user_id == request_context.user.id
    ]
    query = select(Data).join(Data.metric)

    if not note_id and not data_id:
        conditions.extend([
            Data.time >= start_time,
            Data.time <= end_time
        ])
        if tags:
            conditions.append(Metric.tags.any(Tag.display_name.in_(tags)))

        if metric:
            conditions.append(or_(Metric.display_name.like(metric.strip() + '%'),
                 match(inspect(Metric).c.display_name, against=metric.strip())))
    elif data_id:
        conditions.append(Data.id == int(data_id))
    elif note_id:
        query = query.join(Data.note)
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Data.time.desc()) \
        .options(
        joinedload(Data.metric).joinedload(Metric.tags),
        joinedload(Data.metric).joinedload(Metric.schedule)
    )

    data_points = session.scalars(query).unique().all()

    return [{
        constants.id: dp.id,
        constants.note_id: dp.note_id,
        constants.value: float(dp.value),
        constants.units: dp.units,
        constants.origin: dp.origin.value,
        constants.time: dp.time,
        constants.metric: {
            constants.id: dp.metric.id,
            constants.name: dp.metric.display_name,
            constants.tagged: dp.metric.tagged,
            constants.tags: [tag.display_name for tag in dp.metric.tags],
            constants.schedule: {} if dp.metric.schedule is None else {
                constants.id: dp.metric.schedule.id,
                constants.recurrence_schedule: dp.metric.schedule.recurrence_schedule,
                constants.target_value: float(dp.metric.schedule.target_value),
                constants.units: dp.metric.schedule.units,
            }
        }} for dp in data_points], 200


patch_handler = lambda session, update_fields, user_id, id: session.execute(update(Data)
                                                        .values(**update_fields).where(Data.metric_id == Metric.id)
                                                        .where(and_(*[Data.id == id, Metric.user_id == user_id])))

delete_handler = lambda session, user_id, id: session.execute(sql_delete(Data).where(Data.metric_id == Metric.id)
                                                        .where(and_(*[Data.id == id, Metric.user_id == user_id])))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post,
    HttpMethod.PATCH.value: patch_factory(updatable_fileds, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
