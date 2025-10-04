from typing import Dict, Any, List

from sqlalchemy import select, update, and_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload

from backend.lib.db import Tag, normalize_identifier
from backend.lib.func.http import RequestContext, handler_factory, post_factory
from backend.lib.util import HttpMethod

def get(session: Session,request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params

    name = query_params.get('name')

    query = select(Tag).where(Tag.name.like == name + '%').order_by(Tag.name.asc())

    tags = session.scalars(query).all()

    return [{
        'id': tag.id,
        'name': tag.name,
    } for tag in tags], 200

post_handler = lambda context: Tag(**{'name': normalize_identifier(context.body['name'])})

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
})
