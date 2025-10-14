import api
from e2e.common import base_url
from shared import constants

data_path_update = base_url + '/metric/schedule/{id}',
data_path_create = base_url + '/metric/{id}/schedule',


def create(metric_id: int, value: int, units: str,  hour: str, jwt: str) -> int:
    return api.create(
        data_path_create.format(id=metric_id), {
            constants.target_value: value,
            constants.units: units,
            constants.hour: hour,

        }, jwt)


def edit(id: int, value: int, units: str, hour: str, jwt: str):
    return api.edit(
        data_path_update.format(id=id), {
            constants.target_value: value,
            constants.units: units,
            constants.hour: hour,
        }, jwt)


def delete(id: int, jwt: str):
    return api.delete(data_path_update.format(id=id), jwt)

