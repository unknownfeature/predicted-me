from typing import Dict, Any

import requests

from e2e.common import base_url, get_headers, build_query_string
from shared import constants


def create(path: str, body: Dict[str, Any], jwt: str) -> int:
    resp = requests.post(path, headers=get_headers(jwt), json=body)

    assert resp.ok()
    return resp.json()[constants.id]


def edit(path: str, body: Dict[str, Any], jwt: str):
    resp = requests.patch(path, headers=get_headers(jwt), json=body)
    assert resp.ok()


def delete(path: int, jwt: str):
    resp = requests.delete(path, headers=get_headers(jwt))
    assert resp.ok()


def get(path: str, jwt: str, fail_on_not_ok: bool = True) -> Dict[str, Any]:
    resp = requests.get(path, headers=get_headers(jwt), )
    assert not fail_on_not_ok or resp.ok()
    return resp.json() if resp.ok() else None
