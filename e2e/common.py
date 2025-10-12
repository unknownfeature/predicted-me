from typing import Dict

base_url = 'api.predicted.me'

def get_headers(jwt: str) -> Dict[str, str]:
    return {'Authorization': 'Bearer ' + jwt, 'Content-Type': 'application/json'}

def build_query_string(query_params: Dict[str, str]) -> str:
    return '&'.join([f'{k}={v}' for k, v in query_params.items()])