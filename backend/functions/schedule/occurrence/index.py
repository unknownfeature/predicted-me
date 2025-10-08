from sqlalchemy import update, and_, delete as sql_delete

from backend.lib import constants
from backend.lib.db import DataSchedule, OccurrenceSchedule, Task
from backend.lib.func.http import handler_factory, patch_factory, delete_factory, post_factory
from backend.lib.util import HttpMethod

updatable_fields = {constants.minute, constants.hour, constants.day_of_month, constants.month, constants.day_of_week, constants.priority,}

patch_handler = lambda session, update_fields, user_id, id: session.execute(
    update(OccurrenceSchedule).where(OccurrenceSchedule.task_id == Task.id).where(
        and_([OccurrenceSchedule.id == id, Task.user_id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(
    sql_delete(OccurrenceSchedule).where(OccurrenceSchedule.task_id == Task.id).where(
        and_([OccurrenceSchedule.id == id, Task.user_id == user_id])))

post_handler = lambda context, _: DataSchedule(**{f: context.body[f] for f in context.body if f in updatable_fields} | {
    constants.task_id: context.path_params[constants.id], constants.user_id: context.user.id})
handler = handler_factory({
    HttpMethod.POST.value: post_factory(post_handler),
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
