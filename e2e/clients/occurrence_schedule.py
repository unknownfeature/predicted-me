import api
from e2e.common import base_url
from shared import constants

data_path_update = base_url + '/task/schedule/{id}',
data_path_create = base_url + '/task/{id}/schedule',


def create(task_id: int, priority: int, hour: int, jwt: str) -> int:
    return api.create(
        data_path_create.format(id=task_id), {
            constants.priority: priority,
            constants.hour: hour,

        }, jwt)


def edit(id: int, priority: int, hour: int, jwt: str):
    return api.edit(
        data_path_update.format(id=id), {
            constants.priority: priority,
            constants.hour: hour,
        }, jwt)


def delete(id: int, jwt: str):
    return api.delete(data_path_update.format(id=id), jwt)

