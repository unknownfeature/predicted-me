from typing import Dict, Any, List, Tuple

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from backend.lib.db import normalize_identifier, Task
from backend.lib.func.http import RequestContext, handler_factory, post_factory
from backend.lib.util import HttpMethod, get_or_create_tags
from backend.tests.db import session

updatable_fields = {}
def get(session: Session, _, request_context: RequestContext) -> Tuple[List[Dict[str, Any]], int]:
    query_params = request_context.query_params

    summary = query_params.get('summary').strip()



    full_text_condition = func.match(Task.display_summary, Task.description).against(
        summary,
        natural=True
    )

    query = select(Task).where(or_(Task.display_summary.like == summary + '%', full_text_condition)).order_by(Task.display_summary.asc())

    tasks = session.execute(query).all()

    return [{
        'id': m.id,
        'summary': m.display_summary,
        'description': m.description,
    } for m in tasks], 200


def patch(session: Session, request_context: RequestContext) -> (Dict[str, Any], int):
    body = request_context.body
    path_params = request_context.path_params
    id = path_params['id']
    description = body.get('description')
    display_summary = body.get('display_summary')

    if not id:
        return {'error': 'id is required'}, 400
    task_for_update = session.scalar(select(Task).where(and_([Task.id == id, Task.user_id == request_context.user.id])))
    tags_for_update = list(get_or_create_tags(session, set(body.get('tags', []))).values())

    if tags_for_update:
        task_for_update.tags = tags_for_update

    if description:
        task_for_update.description = description

    if display_summary:
        task_for_update.display_summary = display_summary
        tags_for_update.summary = normalize_identifier(display_summary)
    if tags_for_update or description or display_summary:
         session.commit()
    return {'status': 'success'}, 204


post_handler = lambda context, session: Task(user_id=context.user.id, summary=normalize_identifier(context.body['name']),
                                    display_summary=context.body['summary'], description=context.body['description'],
                                    tags=list(get_or_create_tags(session, set(context.body.get('tags', []))).values()))

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch,
    HttpMethod.POST.value: post_factory(post_handler),
})
