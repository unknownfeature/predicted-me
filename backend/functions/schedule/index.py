from sqlalchemy import select, update, and_, delete as sql_delete
from sqlalchemy.orm import Session

from backend.lib.db import DataSchedule, User
from backend.lib.func.http import handler_factory, patch_factory, delete_factory, post_factory
from backend.lib.util import HttpMethod

updatable_fields = {'recurrence_schedule', 'target_value', 'units'}


patch_handler = lambda session, update_fields, user_id, id: session.execute(
    update(DataSchedule).join(DataSchedule.user).where(
        and_([DataSchedule.id == id, User.id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(
    sql_delete(DataSchedule).where(and_([DataSchedule.id == id, DataSchedule.user_id == user_id])))

post_handler = lambda context: DataSchedule(**{f: context.body[f] for f in context.body if f in updatable_fields} | {
                                                          'metric_id': context.path_params['id'], 'user_id': context.user.id})
handler = handler_factory({
    HttpMethod.POST.value: post_factory(post_handler),
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
