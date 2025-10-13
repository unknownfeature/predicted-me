from typing import Dict, Any

import api
from e2e.common import base_url, build_query_string
from shared import constants

occurrence_path_update = base_url + '/task/{task_id}/occurrence/{id}',
occurrence_path_create = base_url + '/task/{task_id}/occurrence',



def create(task_id: str, priority: int, jwt: str) -> int:
    return api.create(
        occurrence_path_create.format(task_id=task_id), {
            constants.priority: priority,

        }, jwt)


def edit(task_id: int, id: int,  priority: int, jwt: str):
    return api.edit(
        occurrence_path_update.format(task_id=task_id, id=id), {
            constants.priority: priority,
        }, jwt)


def delete(task_id: int, id: int, jwt: str):
    return api.delete(  occurrence_path_update.format(task_id=task_id, id=id), jwt)

def get(task_id: int, id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(  occurrence_path_update.format(task_id=task_id, id=id) + f'?{build_query_string(query_params)}', jwt)

