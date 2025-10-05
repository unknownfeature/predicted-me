from typing import Dict, Any, List, Tuple

from sqlalchemy import select, update, and_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Note, Tag, User, Task, Origin, Occurrence
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, delete_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod, get_or_create_task

updatable_fields = {'completed', 'priority', 'time'}


def post(session: Session, request_context: RequestContext) -> Tuple[Dict[str, Any], int]:
    body = request_context.body
    display_summary = body.get('summary')
    task = get_or_create_task(session, display_summary, request_context.user.id)
    data = Occurrence(**{f: body[f] for f in body if f in updatable_fields} | {'origin': Origin.user.value},
                task=task)
    session.add(data)
    session.commit()
    return {'status': 'success'}, 201


def get(session: Session, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    task_id = path_params.get('id')
    note_id = query_params.get('note_id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    search_text = query_params.get('search_text')
    completed = query_params.get('completed')
    end_time, start_time = get_ts_start_and_end(query_params)
    conditions = [
        Task.note.user_id == request_context.user.id
    ]
    query = select(Occurrence).join(Occurrence.task)

    if not note_id and not task_id:
        conditions.extend([
            Occurrence.time >= start_time,
            Occurrence.time <= end_time
        ])

        if tags:
            conditions.append(Task.tags.any(Tag.name.in_(tags)))
        if search_text:
            search_columns = Task.description

            full_text_condition = func.match(*search_columns).against(
                search_text,
                natural=True
            )

            conditions.append(full_text_condition)
        if completed:
            conditions.append(Occurrence.completed == completed)
    elif task_id:
        conditions.append(Task.id == int(task_id))
    elif note_id:
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Occurrence.priority.asc(), Occurrence.time.desc()) \
        .options(
        joinedload(Task.tags)
    )

    occurances = session.scalars(query).unique().all()

    return [{
        'id': occurance.id,
        'note_id': occurance.note_id,
        'priority': occurance.priority,
        'origin': occurance.origin.value,
        'completed': occurance.completed,
        'time': occurance.time,
        'occurance': {
            'id': occurance.task.id,
            'description': occurance.task.description,
            'summary': occurance.task.display_summary,
            'tagged': occurance.task.tagged,
            'tags': [tag.display_name for tag in occurance.task.tags],
            'schedule': {} if occurance.task.schedule is None else {
                'id': occurance.task.schedule.id,
                'recurrence_schedule': occurance.task.schedule.recurrence_schedule,
                'priority': occurance.task.schedule.priority,
            }
        }} for occurance in occurances], 200


patch_handler = lambda session, update_fields, user_id, id: session.execute(update(Occurrence).where(
    and_([Occurrence.id == id, User.id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(sql_delete(Occurrence).where(
    and_([Occurrence.id == id, Occurrence.note.has(Note.user_id == user_id)])))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post,
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})




