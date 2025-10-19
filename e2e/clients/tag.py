from typing import Dict, Any, List

import api
from e2e.common import base_url, build_query_string
from shared import constants

tag_path = base_url + '/tag'


def create(name: str, jwt: str) -> int:
    return api.create(
        tag_path, {
            constants.name: name,
        }, jwt)


def get(jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(tag_path + f'?{build_query_string(query_params)}', jwt)

