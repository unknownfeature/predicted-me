from typing import Dict, Any, List

import requests

from e2e.common import base_url, get_headers, build_query_string
from shared import constants
import api

task_path = base_url + '/task'


def create( description: str, summary: str,  tags: List[str], jwt: str) -> int:
    return api.create(
        task_path, {
            constants.description: description,
            constants.summary: summary,
            constants.tags: tags,
        }, jwt)


def edit(task_id: int,  description: str, summary: str, tags: List[str], jwt: str):
    return api.edit(
        task_path + f'/{task_id}', {
            constants.description: description,
            constants.summary: summary,
            constants.tags: tags,
        }, jwt)



def get(task_id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(task_path + f'/{task_id}?{build_query_string(query_params)}', jwt)

