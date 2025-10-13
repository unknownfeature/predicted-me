from typing import Dict, Any

from e2e.common import base_url, build_query_string

import api
from shared import constants

data_path = base_url + '/data'


def create(metric_id: str, value: float, units: str, time: int, jwt: str) -> int:
    return api.create(
        data_path + f'/{metric_id}', {
            constants.value: value,
            constants.units: units,
            constants.time: time,
        }, jwt)


def edit(data_id: int, value: float, units: str, time: int, jwt: str):
    return api.edit(
        data_path + f'/{data_id}', {
            constants.value: value,
            constants.units: units,
            constants.time: time,
        }, jwt)


def delete(data_id: int, jwt: str):
    return api.delete(data_path + f'/{data_id}', jwt)

def get(data_id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(data_path + f'/{data_id}?{build_query_string(query_params)}', jwt)

