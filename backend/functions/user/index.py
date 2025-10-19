from typing import Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared import constants
from backend.lib.db import User
from backend.lib.func.http import RequestContext, handler_factory, post_factory
from backend.lib.util import HttpMethod


def get(session: Session, context: RequestContext) -> Tuple[Dict[str, str], int]:
    query = select(User).where(User.id == context.user.id)

    user = session.scalars(query).first()
    if not user:
        return {constants.status: constants.error, constants.error: constants.not_found}, 404

    #  todo this is for the future
    return {constants.name: user.name, constants.id: context.user.id}, 200


post_handler = lambda context, _: User(external_id=context.user.external_id)

handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.POST.value: post_factory(post_handler),
})
