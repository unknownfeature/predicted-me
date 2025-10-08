from typing import Tuple, Dict, Any

from sqlalchemy import update, and_, delete as sql_delete, select
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import OccurrenceSchedule, Task
from backend.lib.func.http import handler_factory, patch_factory, delete_factory, RequestContext
from backend.lib.util import HttpMethod

updatable_fields = {constants.minute, constants.hour, constants.day_of_month, constants.month, constants.day_of_week,
                    constants.priority}

patch_handler = lambda session, update_fields, user_id, path_params: session.execute(
    update(OccurrenceSchedule).where(OccurrenceSchedule.task_id == Task.id).where(
        and_(OccurrenceSchedule.id == path_params[constants.id], Task.user_id == user_id)).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(
    sql_delete(OccurrenceSchedule).where(OccurrenceSchedule.task_id == Task.id).where(
        and_(OccurrenceSchedule.id == id, Task.user_id == user_id)))


def post(session: Session, context: RequestContext) -> Tuple[Dict[str, Any], int]:
    id = context.path_params[constants.id]

    task = session.scalars(
        select(Task).where(and_(Task.user_id == context.user.id, Task.id == id))).first()
    if not task:
        return {constants.status: constants.not_found}, 404
    data = OccurrenceSchedule(**{f: context.body[f] for f in context.body if f in updatable_fields} | {
        constants.task_id: context.path_params[constants.id]})
    session.add(data)
    session.commit()
    return {constants.status: constants.success, constants.id: data.id}, 201


handler = handler_factory({
    HttpMethod.POST.value: post,
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
