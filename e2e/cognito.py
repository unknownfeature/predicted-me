import os

import pytest
from dotenv import load_dotenv
from pycognito import Cognito

load_dotenv()

cognito_pool_id = os.getenv('COGNITO_POOL_ID')
cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
admin_user = os.getenv('ADMIN_USER')
admin_user_password = os.getenv('ADMIN_USER_PASSWORD')


def login() -> str:

    cognito_user = Cognito(cognito_pool_id, cognito_client_id, username=admin_user)
    cognito_user.authenticate(password=admin_user_password)

    id_token = cognito_user.id_token
    return id_token

