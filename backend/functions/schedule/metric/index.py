from typing import Tuple, Dict, Any

from sqlalchemy import update, and_, delete as sql_delete, select
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import DataSchedule, Metric, get_utc_timestamp
from backend.lib.func.http import handler_factory, patch_factory, delete_factory, RequestContext
from backend.lib.util import HttpMethod, enrich_schedule_map_with_next_timestamp

updatable_fields = {constants.minute, constants.hour, constants.day_of_month, constants.month, constants.day_of_week,
                    constants.target_value, constants.units}

patch_handler = lambda session, update_fields, user_id, path_params: session.execute(
    update(DataSchedule).where(DataSchedule.metric_id == Metric.id).where(
        and_(DataSchedule.id == path_params[constants.id], Metric.user_id == user_id)).values(
        **enrich_schedule_map_with_next_timestamp(update_fields)))

delete_handler = lambda session, user_id, id: session.execute(
    sql_delete(DataSchedule).where(DataSchedule.metric_id == Metric.id).where(
        and_(DataSchedule.id == id, Metric.user_id == user_id)))


def post(session: Session, context: RequestContext) -> Tuple[Dict[str, Any], int]:
    id = context.path_params[constants.id]

    metric = session.scalars(
        select(Metric).where(and_(Metric.user_id == context.user.id, Metric.id == id))).first()
    if not metric:
        return {constants.status: constants.not_found}, 404
    fields_to_update = {k: v for k, v in context.body.items() if k in updatable_fields}

    data = DataSchedule(**enrich_schedule_map_with_next_timestamp(fields_to_update | {
        constants.metric_id: context.path_params[constants.id]}))
    session.add(data)
    session.commit()
    return {constants.status: constants.success, constants.id: data.id}, 201


handler = handler_factory({
    HttpMethod.POST.value: post,
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
