from typing import Dict, Tuple

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from shared import constants
from backend.lib.db import User
from backend.lib.func.http import RequestContext, handler_factory, post_factory, patch_factory
from backend.lib.util import HttpMethod

updatable_fields = {constants.links_enabled, constants.tasks_enabled, constants.name}


def get(session: Session, context: RequestContext) -> Tuple[Dict[str, str], int]:
    query = select(User).where(User.id == context.user.id)

    user = session.scalars(query).first()
    if not user:
        return {constants.status: constants.error, constants.error: constants.not_found}, 404

    #  todo this is for the future
    return {constants.name: user.name, constants.links_enabled: user.links_enabled,
            constants.tasks_enabled: user.tasks_enabled, constants.id: context.user.id}, 200


post_handler = lambda context, _: User(external_id=context.user.external_id, name=context.body.get(constants.name),
                                       links_enabled=context.body.get(constants.links_enabled),
                                       tasks_enabled=context.body.get(constants.tasks_enabled))

patch_handler = lambda session, update_fields, user_id, path_params: session.execute(update(User)
                                                                                     .values(**update_fields)
                                                                                     .where(User.id == user_id))
handler = handler_factory({
    HttpMethod.GET.value: get,
    HttpMethod.PATCH.value: patch_factory(updatable_fields, patch_handler),
    HttpMethod.POST.value: post_factory(post_handler),
})
