import pytest

from e2e.clients import user
from e2e.cognito import login


@pytest.fixture(scope='session')
def jwt():
    jwt =  login()
    user.create(jwt)
