from typing import Dict, Any, List, Tuple

from sqlalchemy import select, update, and_, delete as sql_delete, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session, joinedload

from backend.lib import constants
from backend.lib.db import Note, Tag, Task, Origin, Occurrence
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, delete_factory, get_offset_and_limit, \
    get_ts_start_and_end
from backend.lib.util import HttpMethod

updatable_fields = {constants.completed, constants.priority, constants.time}


def post(session: Session, request_context: RequestContext) -> Tuple[Dict[str, Any], int]:
    body = request_context.body
    id = request_context.path_params[constants.id]
    task = session.scalars(
        select(Task).where(and_(*[Task.user_id == request_context.user.id, Task.id == id]))).first()
    if not task:
        return {constants.status: constants.not_found}, 404

    occurrence = Occurrence(**{f: body[f] for f in body if f in updatable_fields} | {
        constants.origin: Origin.user.value},
                            task=task)
    session.add(occurrence)
    session.commit()
    return {constants.status: constants.success, constants.id: occurrence.id}, 201


def get(session: Session, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    occurrence_id = path_params.get(constants.id)
    note_id = query_params.get(constants.note_id)
    tags = query_params.get(constants.tags).split(constants.params_delim) if constants.tags in query_params else []
    task = query_params.get(constants.task, constants.empty).strip()
    completed = query_params.get(constants.completed)
    start_time, end_time = get_ts_start_and_end(query_params)
    offset, limit = get_offset_and_limit(query_params)
    conditions = [
        Task.user_id == request_context.user.id
    ]
    query = select(Occurrence).join(Occurrence.task)

    if not note_id and not occurrence_id:
        conditions.extend([
            Occurrence.time >= start_time,
            Occurrence.time <= end_time
        ])

        if tags:
            conditions.append(Task.tags.any(Tag.display_name.in_(tags)))

        if task:
            conditions.append(match(inspect(Task).c.display_summary, inspect(Task).c.description,
                                    against=task).in_natural_language_mode())

        if completed:
            conditions.append(Occurrence.completed == completed)

    elif occurrence_id:
        conditions.append(Occurrence.id == int(occurrence_id))
    elif note_id:
        query = query.join(Occurrence.note)
        conditions.append(Note.id == int(note_id))
    query = (query.where(and_(*conditions)).offset(offset).limit(limit).order_by(Occurrence.priority.desc(), Occurrence.time.desc())
    .options(
        joinedload(Occurrence.task)
        .joinedload(Task.tags), joinedload(Occurrence.task)
        .joinedload(Task.schedule)
    ))

    occurrences = session.scalars(query).unique().all()

    return [{
        constants.id: occurrence.id,
        constants.note_id: occurrence.note_id,
        constants.priority: occurrence.priority,
        constants.origin: occurrence.origin.value,
        constants.completed: occurrence.completed,
        constants.time: occurrence.time,
        constants.task: {
            constants.id: occurrence.task.id,
            constants.description: occurrence.task.description,
            constants.summary: occurrence.task.display_summary,
            constants.tagged: occurrence.task.tagged,
            constants.tags: [tag.display_name for tag in occurrence.task.tags],
            constants.schedule: {} if occurrence.task.schedule is None else {
                constants.id: occurrence.task.schedule.id,
                constants.recurrence_schedule: occurrence.task.schedule.recurrence_schedule,
                constants.priority: occurrence.task.schedule.priority,
            }
        }} for occurrence in occurrences], 200


patch_handler = lambda session, update_fields, user_id, id: session.execute(update(Occurrence)
                                                                            .values(**update_fields).where(
    Occurrence.task_id == Task.id)
                                                                            .where(
    and_(*[Occurrence.id == id, Task.user_id == user_id])))

delete_handler = lambda session, user_id, id: session.execute(
    sql_delete(Occurrence).where(Occurrence.task_id == Task.id)
    .where(and_(*[Occurrence.id == id, Task.user_id == user_id])))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post,
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
