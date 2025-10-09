from typing import Dict, Any, List, Tuple

from sqlalchemy import select, and_, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.constants import id_is_required
from backend.lib.db import normalize_identifier, Metric, Tag
from backend.lib.func.http import RequestContext, handler_factory, post_factory, get_offset_and_limit
from backend.lib.util import HttpMethod, get_or_create_tags


def get(session: Session, context: RequestContext) -> Tuple[List[Dict[str, Any]]|Dict[str, str], int]:
    path_params = context.path_params

    id = path_params.get(constants.id)

    query_params = context.query_params
    offset, limit = get_offset_and_limit(query_params)

    text = query_params.get(constants.name, constants.empty).strip()
    tags = query_params.get(constants.tags).split(constants.params_delim) if constants.tags in query_params else []

    conditions = [Metric.user_id == context.user.id]
    if id:
        conditions.append(Metric.id == id)
    else:
        if tags:
           conditions.append(Metric.tags.any(Tag.display_name.in_(tags)))
        if text:
           conditions.append(match(inspect(Metric).c.display_name,
                                     against=text).in_natural_language_mode(), )
    query = (select(Metric).where(and_(*conditions))

             .offset(offset)
             .limit(limit)
             .order_by(Metric.display_name.asc()))

    metrics = session.scalars(query).unique().all()

    return [{
        constants.id: metric.id,
        constants.name: metric.display_name,
        constants.tags: [tag.display_name for tag in metric.tags],
    } for metric in metrics], 200


def patch(session: Session, context: RequestContext) -> (Dict[str, Any], int):
    body = context.body
    path_params = context.path_params

    id = path_params[constants.id]

    description = body.get(constants.description)
    display_name = body.get(constants.name)

    if not id:
        return {constants.error: id_is_required}, 400

    metric_for_update = session.scalar(select(Metric).where(and_(Metric.id == id, Metric.user_id == context.user.id)))
    tags_for_update = list(get_or_create_tags(context.user.id, session, set(body.get(constants.tags, []))).values())
    if not metric_for_update:
        return {constants.status: constants.error, constants.error: constants.not_found}, 400
    if tags_for_update:
        metric_for_update.tags = tags_for_update
        metric_for_update.tagged = True

    if description:
        metric_for_update.description = description

    if display_name:
        metric_for_update.display_name = display_name
        metric_for_update.name = normalize_identifier(display_name)
    if tags_for_update or description or display_name:
         session.commit()
    return {constants.status: constants.success}, 204


post_handler = lambda context, session: Metric(user_id=context.user.id,
                                             name=normalize_identifier(context.body[constants.name]),
                                    display_name=context.body[constants.name],
                                               tagged = len(context.body.get(constants.tags, []) ) > 0,
                                    tags=list(get_or_create_tags(context.user.id, session, set(context.body.get(constants.tags, []))).values()))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch,
    HttpMethod.POST.value: post_factory(post_handler),
})
