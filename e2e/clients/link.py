from typing import Dict, Any, List

import requests

from e2e.common import base_url, get_headers, build_query_string
from shared import constants
import api

link_path = base_url + '/link'


def create(url: str, description: str, summary: str, tags: List[str], jwt: str) -> int:
    return api.create(
        link_path, {
            constants.url: url,
            constants.description: description,
            constants.summary: summary,
            constants.tags: tags,
        }, jwt)


def edit(link_id: int, url: str, description: str, summary: str, tags: List[str], jwt: str):
    return api.edit(
        link_path + f'/{link_id}', {
            constants.url: url,
            constants.description: description,
            constants.summary: summary,
            constants.tags: tags,
        }, jwt)


def delete(link_id: int, jwt: str):
    return api.delete(link_path + f'/{link_id}', jwt)

def get(link_id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(link_path + f'/{link_id}?{build_query_string(query_params)}', jwt)

