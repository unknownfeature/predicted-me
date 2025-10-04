from typing import Dict, Any, List

from sqlalchemy import select, update, and_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload, selectinload

from backend.lib.db import Tag, Metric, User, get_utc_timestamp_int
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, post_factory
from backend.lib.util import HttpMethod, merge_tags


# should be fulltext search on the human readable name todo
def get(session: Session, user_id: int, request_context: RequestContext) -> tuple[Dict[str, Any], int]:

    query = select(User).where(User.id == user_id)

    user = session.scalars(query).first()

    return {'name': user.name, 'id': user_id}, 200


post_handler = lambda context: User(**{'external_id': context.user.external_id, 'time': get_utc_timestamp_int()})

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory( post_handler),
})
