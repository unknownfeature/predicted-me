from typing import Dict, Any, List, Union

from sqlalchemy import select, update, and_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Note, Tag, User, Task
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, delete_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod



def get(session: Session, user_id, request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    task_id = path_params.get('id')
    note_id = query_params.get('note_id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    search_text = query_params.get('search_text')
    completed = query_params.get('completed')
    end_time, start_time = get_ts_start_and_end(query_params)
    conditions = [
        Task.note.user_id == user_id
    ]
    query = select(Task)

    if not note_id and not task_id:
        conditions.extend([
            Task.time >= start_time,
            Task.time <= end_time
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
            conditions.append(Task.completed == completed)
    elif task_id:
        conditions.append(Task.id == int(task_id))
    elif note_id:
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Task.priority.asc(), Task.time.desc()) \
        .options(
        joinedload(Task.tags)
    )

    tasks = session.scalars(query).all()

    return [{
        'id': task.id,
        'note_id': task.note_id,
        'priority': task.priority,
        'description': task.description,
        'origin': task.origin.value,
        'tagged': task.tagged,
        'completed': task.completed,
        'time': task.time,
        'tags': [tag for tag in task.tags],
    } for task in tasks], 200



patch_handler = lambda session, update_fields, user_id, id: session.execute(update(Task).where(and_([Task.id == id, User.id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(sql_delete(Task).where(and_([Task.id == id, Task.note.has(Note.user_id == user_id)])))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch_factory({'url', 'description', 'time'}, patch_handler),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
