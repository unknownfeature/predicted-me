from importlib.metadata.diagnose import inspect
from typing import Dict, Any, List, Tuple

from sqlalchemy import select, and_
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import Metric, normalize_identifier
from backend.lib.func.http import RequestContext, handler_factory, post_factory
from backend.lib.util import HttpMethod, get_or_create_tags


def get(session: Session, _, request_context: RequestContext) -> Tuple[List[Dict[str, Any] | Dict[str, str]], int]:
    query_params = request_context.query_params

    name = query_params.get(constants.name, constants.empty).strip()

    if not name:
        return {constants.error:  constants.name_is_required}, 400

    query = select(Metric).where( match(inspect(Metric).c.display_name, against=name).in_natural_language_mode()).order_by(
        Metric.display_name.asc())

    metrics = session.execute(query).all()

    return [{
        constants.id: m.id,
        constants.name: m.name,
    } for m in metrics], 200


def patch(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
    body = request_context.body
    path_params = request_context.path_params
    id = path_params.get(constants.id)
    name = body.get(constants.name)

    if not id:
        return {constants.error: constants.id_is_required}, 400
    metric_for_update = session.scalar(
        select(Metric).where(and_([Metric.id == id, Metric.user_id == request_context.user.id])))

    tags_for_update = list(get_or_create_tags(session, set(body.get(constants.tags, []))).values())

    if tags_for_update:
        metric_for_update.tags = tags_for_update

    if name:
        metric_for_update.display_name = name
        tags_for_update.summary = normalize_identifier(name)
    if tags_for_update or name:
        session.commit()
    return {constants.status: constants.success}, 204


post_handler = lambda context, session: Metric(user_id=context.user.id, name=normalize_identifier(context.body.get(constants.name)),
                                    display_name=context.body.get(constants.name),
                                    tags=list(get_or_create_tags(session, set(context.body.get(constants.tags, []))).values()))


handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch,
    HttpMethod.POST.value: post_factory(post_handler),
})
