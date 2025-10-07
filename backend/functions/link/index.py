from typing import Dict, Any, List, Tuple

from sqlalchemy import select, and_, delete as sql_delete, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session, joinedload

from backend.lib import constants
from backend.lib.db import Note, Tag, Link, Origin
from backend.lib.func.http import RequestContext, handler_factory, delete_factory, post_factory, get_offset_and_limit, get_ts_start_and_end
from backend.lib.util import  HttpMethod, get_or_create_tags


def get(session: Session, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params
    path_params = request_context.path_params

    link_id = path_params.get(constants.id)
    note_id = query_params.get(constants.note_id)

    tags = query_params.get(constants.tags).split(constants.params_delim) if constants.tags in query_params else []
    link = query_params.get(constants.link, constants.empty).strip()
    start_time, end_time = get_ts_start_and_end(query_params)
    offset, limit = get_offset_and_limit(query_params)

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
            conditions.append(Link.tags.any(Tag.display_name.in_(tags)))

        if link:
            conditions.append(match(inspect(Link).c.description, inspect(Link).c.url, against=link).in_natural_language_mode())


    elif link_id:
        conditions.append(Link.id == int(link_id))

    elif note_id:
        query = query.join(Link.note)
        conditions.append(Note.id == int(note_id))

    query = (query.where(and_(*conditions))
             .offset(offset)
             .limit(limit)
             .order_by(Link.time.desc()).options(joinedload(Link.tags)))


    links = session.scalars(query).unique().all()

    return [{
        constants.id: link.id,
        constants.note_id: link.note_id,
        constants.url: link.url,
        constants.description: link.description,
        constants.origin: link.origin.value,
        constants.tagged: link.tagged,
        constants.time: link.time,
        constants.tags: [tag.display_name for tag in link.tags],
    } for link in links], 200

def patch(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
    body = request_context.body
    path_params = request_context.path_params
    id = path_params.get(constants.id)

    description = body.get(constants.description)
    url = body.get(constants.url)

    if not id:
        return {constants.error:  constants.id_is_required}, 400

    link_for_update = session.scalar(select(Link).where(and_(*[Link.id == id, Link.user_id == request_context.user.id])))

    if not link_for_update:
        return {constants.error: constants.not_found}, 404

    tags_for_update = list(get_or_create_tags(session, set(body.get(constants.tags, []))).values())

    if tags_for_update:
        link_for_update.tags = tags_for_update

    if description:
        link_for_update.description = description

    if url:
        link_for_update.url = url

    if tags_for_update or description or url:
         session.add(link_for_update)
         session.commit()

    return {constants.status: constants.success}, 204


delete_handler = lambda session, user_id, id: session.execute(sql_delete(Link).where(
                                                     and_(*[Link.id == id, Link.user_id == user_id])))


post_handler = lambda context, session: Link(user_id=context.user.id, url=context.body[constants.url],
                                    description=context.body[constants.description], origin=Origin.user.value,
                                    tags=list(get_or_create_tags(session, set(context.body.get(constants.tags, []))).values()))
handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
    HttpMethod.PATCH.value: patch,
    HttpMethod.DELETE.value: delete_factory(delete_handler),

})
