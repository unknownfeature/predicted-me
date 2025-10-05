from typing import Dict, Any, List

from sqlalchemy import select, update, and_, delete as sql_delete, func, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload

from backend.lib.db import Tag, Metric, User, get_utc_timestamp
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, post_factory
from backend.lib.util import HttpMethod, merge_tags


def get(session: Session, request_context: RequestContext) -> Tuple[Dict[str, Any], int]:
    query = select(User).where(User.id == request_context.user.id)

    user = session.execute(query).first()

    return {'name': user.name, 'id': request_context.user.id}, 200


post_handler = lambda context, _: User(**{'external_id': context.user.external_id})

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
})
