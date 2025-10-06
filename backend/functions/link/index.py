from typing import Dict, Any, List, Tuple

from sqlalchemy import select, update, and_, delete as sql_delete, func, or_, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session, joinedload

from backend.lib import constants
from backend.lib.db import Note, Tag, User, Link, get_utc_timestamp
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, delete_factory, post_factory
from backend.lib.util import get_ts_start_and_end, HttpMethod, get_or_create_tags

updatable_fields = {'url', 'description', 'time'}


def get(session: Session, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    link_id = path_params.get('id')
    note_id = query_params.get('note_id')
    tags = query_params.get('tags').split(constants.params_delim) if 'tags' in query_params else []
    link = query_params.get('link')
    start_time, end_time = get_ts_start_and_end(query_params)
    conditions = [
        Link.user_id == request_context.user.id
    ]
    query = select(Link)

    if not note_id and not link_id:
        conditions.extend([
            Link.time >= start_time,
            Link.time <= end_time
        ])

        if tags:
            conditions.append(Link.tags.any(Tag.name.in_(tags)))
        if link:
            striped = link.strip()
            conditions.append(or_(Link.description.like(striped + constants.like),
                                  Link.url.like(striped + constants.like),
                                  match(inspect(Link).c.description, inspect(Link).c.url, against=striped)))

    elif link_id:
        conditions.append(Link.id == int(link_id))
    elif note_id:
        query = query.join(Link.note)
        conditions.append(Note.id == int(note_id))
    query = query.where(and_(*conditions)) \
        .order_by(Link.time.desc()) \
        .options(
        joinedload(Link.tags)
    )

    links = session.scalars(query).unique().all()

    return [{
        'id': link.id,
        'note_id': link.note_id,
        'url': link.url,
        'description': link.description,
        'origin': link.origin.value,
        'tagged': link.tagged,
        'time': link.time,
        constants.tags: [tag.display_name for tag in link.tags],
    } for link in links], 200

def patch(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
    body = request_context.body
    path_params = request_context.path_params
    id = path_params['id']
    description = body.get('description')
    url = body.get('url')

    if not id:
        return {'error': 'id is required'}, 400
    link_for_update = session.scalar(select(Link).where(and_([Link.id == id, Link.user_id == request_context.user.id])))
    tags_for_update = list(get_or_create_tags(session, set(body.get('tags', []))).values())

    if tags_for_update:
        link_for_update.tags = tags_for_update

    if description:
        link_for_update.description = description

    if url:
        link_for_update.url = url
    if tags_for_update or description or url:
         session.commit()
    return {'status': 'success'}, 204



delete_handler = lambda session, user_id, id: session.execute(sql_delete(Link).where(
                                                     and_([Link.id == id, Link.note.has(Note.user_id == user_id)])))


post_handler = lambda context, session: Link(user_id=context.user.id, url=context.body['url'],
                                    description=context.body['description'],
                                    tags=list(get_or_create_tags(session, set(context.body.get('tags', []))).values()))
handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
    HttpMethod.PATCH.value: patch,
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
