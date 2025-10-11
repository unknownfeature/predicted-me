import os
import traceback

import boto3

from backend.lib import constants
from shared.variables import Env

secrets_client = boto3.client(constants.secretsmanager)
cognito_client = boto3.client(constants.cognito_idp)

user_pool_id = os.getenv(Env.cognito_pool_id)
username = os.getenv(Env.admin_user)
password_secret_arn = os.getenv(Env.admin_secret_arn)

def handler(event, _):
    request_type = event[constants.request_type]

    if request_type == constants.create_request_type:
        return on_create()

    return {constants.resource_status: constants.resource_success}


def on_create():
    try:
        secret_response = secrets_client.get_secret_value(SecretId=password_secret_arn)
        password = secret_response[constants.secret_string]

        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=password,
            UserAttributes=[
                {constants.cognito_name: constants.cognito_email, constants.cognito_value: username},
                {constants.cognito_name: constants.cognito_email_verified, constants.cognito_value: str(True)},
            ],
            MessageAction=constants.message_action_suppress,
        )
        return {constants.resource_status: constants.resource_success}

    except Exception as e:
        traceback.print_exc()
        return {constants.resource_status: constants.resource_failed, constants.resource_reason: str(e)}