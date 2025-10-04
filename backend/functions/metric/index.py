from typing import Dict, Any, List

from sqlalchemy import select, update, and_, or_, delete as sql_delete, func
from sqlalchemy.orm import Session, joinedload, selectinload

from backend.lib.db import Metric, normalize_identifier
from backend.lib.func.http import RequestContext, handler_factory, patch_factory, post_factory
from backend.lib.util import HttpMethod, merge_tags

# should be fulltext search on the human readable name todo
def get(session: Session, _, request_context: RequestContext) -> tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params

    name = query_params.get('name')

    full_text_condition = func.match(*Metric.display_name).against(
        name,
        natural=True
    )

    query = select(Metric).where(or_([Metric.name.like == name + '%', full_text_condition])).order_by(Metric.name.asc())

    metrics = session.scalars(query).all()

    return [{
        'id': m.id,
        'name': m.name,
    } for m in metrics], 200


patch_handler = lambda session, update_fields, user_id, id: merge_tags(session, [{'id': id, 'tags': [t.lower() for t in update_fields['tags']]}], lambda: select(Metric)
               .join(Metric.data_points).where(and_([Metric.id  == id, Metric.user_id == user_id])
    ).options(selectinload(Metric.tags)))

post_handler = lambda context: Metric(**{'user_id': context.user.id, 'name': normalize_identifier(context.body['name']), 'display_name': context.body['name']})

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch_factory({'tags'}, patch_handler),
    HttpMethod.POST.value: post_factory(post_handler),
})
