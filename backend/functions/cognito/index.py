import os
import traceback

import boto3

from shared import constants
from shared.variables import *

secrets_client = boto3.client(constants.secretsmanager)
cognito_client = boto3.client(constants.cognito_idp)

user_pool_id = os.getenv(cognito_pool_id)
username = os.getenv(admin_user)
password_secret_arn = os.getenv(admin_secret_arn)
tmp_password_secret_arn = os.getenv(admin_tmp_secret_arn)

def handler(event, _):
    request_type = event[constants.request_type]

    if request_type == constants.create_request_type:
        return on_create()

    return {constants.resource_status: constants.resource_success}


def on_create():
    try:
        tmp_secret_response = secrets_client.get_secret_value(SecretId=tmp_password_secret_arn)
        tmp_password = tmp_secret_response[constants.secret_string]

        print('creating admin user')
        create_user_response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=tmp_password,
            UserAttributes=[
                {constants.cognito_name: constants.cognito_email, constants.cognito_value: username},
                {constants.cognito_name: constants.cognito_email_verified, constants.cognito_value: str(True)},
            ],
            MessageAction=constants.message_action_suppress,
        )

        print(create_user_response)

        secret_response = secrets_client.get_secret_value(SecretId=password_secret_arn)
        password = secret_response[constants.secret_string]
        print('updating admin user password')

        update_password_response = cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )

        print(update_password_response)
        return {constants.resource_status: constants.resource_success}

    except Exception as e:
        traceback.print_exc()
        return {constants.resource_status: constants.resource_failed, constants.resource_reason: str(e)}