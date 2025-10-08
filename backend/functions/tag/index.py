from typing import Dict, Any, List, Tuple

from sqlalchemy import select, and_, inspect
from sqlalchemy.dialects.mysql import match
from sqlalchemy.orm import Session

from backend.lib import constants
from backend.lib.db import Tag, normalize_identifier
from backend.lib.func.http import RequestContext, handler_factory, post_factory, get_offset_and_limit
from backend.lib.util import HttpMethod


def get(session: Session,context: RequestContext) -> Tuple[List[Dict[str, Any]]|Dict[str, str], int]:
    query_params = context.query_params

    name = query_params.get(constants.name)


    offset, limit = get_offset_and_limit(query_params)

    conditions = [Tag.user_id == context.user.id]
    if name:
        conditions.append(match(inspect(Tag).c.display_name,
                                     against=name).in_natural_language_mode(), )

    query = (select(Tag).where(and_(*conditions))

             .offset(offset)
             .limit(limit)
             .order_by(Tag.name.asc()))

    tags = session.scalars(query).all()

    return [{
        constants.id: tag.id,
        constants.name: tag.display_name,
    } for tag in tags], 200


post_handler = lambda context, _: Tag(display_name=context.body[constants.name], name=normalize_identifier(context.body[constants.name]),  user_id=context.user.id)

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
})
