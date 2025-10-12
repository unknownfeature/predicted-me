from typing import Dict

base_url = 'api.predicted.me'

def get_headers(jwt: str) -> Dict[str, str]:
    return {'Authorization': 'Bearer ' + jwt, 'Content-Type': 'application/json'}