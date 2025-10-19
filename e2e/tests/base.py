from e2e.clients import user
from e2e.cognito import login


def setup() -> str:
    jwt = login()
    existing = user.get(jwt)
    if not existing:
        user.create(jwt)
    return jwt

