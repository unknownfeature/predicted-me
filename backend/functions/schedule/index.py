from typing import Dict, Union

from sqlalchemy import select, update, and_, delete as sql_delete
from sqlalchemy.orm import Session

from backend.lib.db import DataSchedule, User
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, delete_factory
from backend.lib.util import HttpMethod

def post(session: Session, user_id, request_context: RequestContext) -> tuple[Dict[str, Union[int, str]], int]:
    query_params = request_context.query_params
    body = request_context.body
    metric_id = query_params['metric_id']
    schedule_exists = session.execute(select(DataSchedule).join(DataSchedule.user).where(
        and_([DataSchedule.metric_id == metric_id, User.id == user_id]))).first()

    if schedule_exists:
        return {'status': 'error', 'message': f'Schedule with id {metric_id} exists.'}, 403

    update_fields = {f: body[f] for f in body if f in {'recurrence_schedule', 'target_value', 'units'}} | {
        'metric_id': metric_id, 'user_id': user_id}
    schedule = DataSchedule(
        **update_fields)

    session.add(schedule)
    session.flush()

    return {'status': 'success', 'id': schedule.id}, 201


patch_handler = lambda session, update_fields, user_id, id: session.execute(update(DataSchedule).join(DataSchedule.user).where(
                                                  and_([DataSchedule.id == id, User.id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(sql_delete(DataSchedule).where(and_([DataSchedule.id == id, DataSchedule.user_id == user_id])))

handler = handler_factory({
    HttpMethod.POST.value: post,
    HttpMethod.PATCH.value: patch_factory( {'recurrence_schedule', 'target_value', 'units'}, patch_handler
                                          ),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})




