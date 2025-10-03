from typing import Dict, Any, List

from sqlalchemy import select, update, and_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Note, Tag, User, Link
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, delete_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod


def get(session: Session, user_id: int, request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    link_id = path_params.get('id')
    note_id = query_params.get('note_id')
    tags = query_params.get('tags').split(',') if 'tags' in query_params else []
    search_text = query_params.get('search_text')
    end_time, start_time = get_ts_start_and_end(query_params)
    conditions = [
        Link.note.user_id == user_id
    ]
    query = select(Link)

    if not note_id and not link_id:
        conditions.extend([
            Link.time >= start_time,
            Link.time <= end_time
        ])

        if tags:
            conditions.append(Link.tags.any(Tag.name.in_(tags)))
        if search_text:
            search_columns = Link.description, Link.url

            full_text_condition = func.match(*search_columns).against(
                search_text,
                natural=True
            )

            conditions.append(full_text_condition)
    elif link_id:
        conditions.append(Link.id == int(link_id))
    elif note_id:
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Link.time.desc()) \
        .options(
        joinedload(Link.tags)
    )

    links = session.scalars(query).all()

    return [{
        'id': link.id,
        'note_id': link.note_id,
        'url': link.url,
        'description': link.description,
        'origin': link.origin.value,
        'tagged': link.tagged,
        'time': link.time,
        'tags': [tag for tag in link.tags],
    } for link in links], 200


patch_handler = lambda session, update_fields, user_id, id: session.execute(update(Link).where(
                                                     and_([Link.id == id, User.id == user_id])).values(**update_fields))

delete_handler = lambda session, user_id, id: session.execute(sql_delete(Link).where(
                                                     and_([Link.id == id, Link.note.has(Note.user_id == user_id)])))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch_factory({'url', 'description', 'time'}, patch_handler
                                          ),
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
