from typing import Dict, Any

import api
from e2e.common import base_url

user_path = base_url + '/user'


def create(jwt: str) -> int:
    return api.create(
        user_path, {
        }, jwt)


def get(jwt: str) -> Dict[str, Any]:
    return api.get(user_path, jwt, fail_on_not_ok=False)
