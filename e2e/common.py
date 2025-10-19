import asyncio
import datetime
from typing import Dict, Callable, Any

base_url = 'https://api.predicted.me'


def get_headers(jwt: str) -> Dict[str, str]:
    return {'Authorization': 'Bearer ' + jwt, 'Content-Type': 'application/json'}


def build_query_string(query_params: Dict[str, str]) -> str:
    return '&'.join([f'{k}={v}' for k, v in query_params.items()])


def get_utc_timestamp() -> int:
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp())


async def wait_for_a_condition_to_be_true(predicate: Callable[[Any], bool], provider: Callable[[], Any],
                                          failing_message: str, retries: int = 3, sleep_time_sec: int = 1):
    retries_left = retries
    result_data = provider()

    while not predicate(result_data) and retries_left > 0:
        await asyncio.sleep(sleep_time_sec)
        result_data = provider()
        retries_left -= 1

    assert predicate(result_data), failing_message
