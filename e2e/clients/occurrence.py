from typing import Dict, Any

import api
from e2e.common import base_url, build_query_string
from shared import constants
occurrence_path_get = base_url + '/occurrence',
occurrence_path_update = base_url + '/occurrence/{id}',
occurrence_path_create = base_url + '/task/{task_id}/occurrence',


def create(task_id: int, priority: int, jwt: str) -> int:
    return api.create(
        occurrence_path_create.format(task_id=task_id), {
            constants.priority: priority,

        }, jwt)


def edit(id: int, priority: int, jwt: str):
    return api.edit(
        occurrence_path_update.format( id=id), {
            constants.priority: priority,
        }, jwt)


def delete(id: int, jwt: str):
    return api.delete(occurrence_path_update.format(id=id), jwt)


def get(id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get((occurrence_path_update.format(id=id) if id else occurrence_path_get) + f'?{build_query_string(query_params)}', jwt)
