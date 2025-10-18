from typing import Dict, Any, List, Tuple

from sqlalchemy import select, and_, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session

from shared import constants
from backend.lib.db import normalize_identifier, Task, Tag
from backend.lib.func.http import RequestContext, handler_factory, post_factory, get_offset_and_limit
from backend.lib.util import HttpMethod, get_or_create_tags


def get(session: Session, context: RequestContext) -> Tuple[List[Dict[str, Any]]|Dict[str, str], int]:
    path_params = context.path_params

    id = path_params.get(constants.id)

    query_params = context.query_params
    offset, limit = get_offset_and_limit(query_params)

    text = query_params.get(constants.text, constants.empty).strip()
    tags = query_params.get(constants.tags).split(constants.params_delim) if constants.tags in query_params else []

    conditions = [Task.user_id == context.user.id]
    if id:
        conditions.append(Task.id == id)
    else:
        if tags:
           conditions.append(Task.tags.any(Tag.display_name.in_(tags)))
        if text:
           conditions.append(match(inspect(Task).c.display_summary, inspect(Task).c.description,
                                     against=text).in_natural_language_mode(), )
    query = (select(Task).where(and_(*conditions))

             .offset(offset)
             .limit(limit)
             .order_by(Task.display_summary.asc()))

    tasks = session.scalars(query).unique().all()

    return [{
        constants.id: task.id,
        constants.summary: task.display_summary,
        constants.description: task.description,
        constants.tags: [tag.display_name for tag in task.tags],
    } for task in tasks], 200


def patch(session: Session, context: RequestContext) -> (Dict[str, Any], int):
    body = context.body
    path_params = context.path_params

    id = path_params[constants.id]

    description = body.get(constants.description)
    display_summary = body.get(constants.summary)

    if not id:
        return {constants.error: constants.id_is_required}, 400

    task_for_update = session.scalar(select(Task).where(and_(Task.id == id, Task.user_id == context.user.id)))
    tags_for_update = list(get_or_create_tags(context.user.id, session, set(body.get(constants.tags, []))).values())
    if not task_for_update:
        return {constants.status: constants.error, constants.error: constants.not_found}, 400
    if tags_for_update:
        task_for_update.tags = tags_for_update
        task_for_update.tagged = True

    if description:
        task_for_update.description = description

    if display_summary:
        task_for_update.display_summary = display_summary
        task_for_update.summary = normalize_identifier(display_summary)
    if tags_for_update or description or display_summary:
         session.commit()
    return {constants.status: constants.success}, 204


post_handler = lambda context, session: Task(user_id=context.user.id,
                                             summary=normalize_identifier(context.body[constants.summary]),
                                    display_summary=context.body[constants.summary],
                                             description=context.body[constants.description],
                                             tagged=len(context.body.get(constants.tags, [])) > 0,
                                    tags=list(get_or_create_tags(context.user.id, session, set(context.body.get(constants.tags, []))).values()))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch,
    HttpMethod.POST.value: post_factory(post_handler),
})
