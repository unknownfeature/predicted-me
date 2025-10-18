from typing import Dict, Any

from e2e.common import base_url, build_query_string
from shared import constants

data_path_get = base_url + '/data',
data_path_update = base_url + '/data/{id}',
data_path_create = base_url + '/metric/{metric_id}/data',


def create(metric_id: int, value: float, units: str, time: int, jwt: str) -> int:
    return api.create(
        data_path_create.format(metric_id=metric_id), {
            constants.value: value,
            constants.units: units,
            constants.time: time,
        }, jwt)


def edit(id: int, value: float, units: str, time: int, jwt: str):
    return api.edit(
        data_path_update.format(id=id), {
            constants.value: value,
            constants.units: units,
            constants.time: time,
        }, jwt)


def delete(id: int, jwt: str):
    return api.delete(data_path_update.format(id=id), jwt)


def get(id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:

    return api.get((data_path_update.format(id=id) if id else data_path_get)  + f'?{build_query_string(query_params)}', jwt)


