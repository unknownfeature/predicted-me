import pytest

from e2e.cognito import login


@pytest.fixture(scope='session')
async def jwt():
    return login()
