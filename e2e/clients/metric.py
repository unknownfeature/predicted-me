from typing import Dict, Any, List

import api
from e2e.common import base_url, build_query_string
from shared import constants

metric_path = base_url + '/metric'


def create(name: str,  tags: List[str], jwt: str) -> int:
    return api.create(
        metric_path, {
            constants.name: name,
            constants.tags: tags,
        }, jwt)


def edit(metric_id: int,  name: str, tags: List[str], jwt: str):
    return api.edit(
        metric_path + f'/{metric_id}', {
            constants.name: name,
            constants.tags: tags,
        }, jwt)



def get(metric_id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(metric_path + f'/{metric_id}?{build_query_string(query_params)}', jwt)

