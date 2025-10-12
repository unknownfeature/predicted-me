import base64
import hashlib
import hmac

import boto3


def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    message = bytes(username + client_id, 'utf-8')
    key = bytes(client_secret, 'utf-8')
    hmac_hash = hmac.new(key, message, digestmod=hashlib.sha256)
    return base64.b64encode(hmac_hash.digest()).decode()


def login(email: str, password: str, client_id: str, client_secret: str) -> str:

    cognito_client = boto3.client("cognito-idp")

    secret_hash = get_secret_hash(email, client_id, client_secret)


    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': email,
            'PASSWORD': password,
            'SECRET_HASH': secret_hash
        }
    )

    auth_result = auth_response.get('AuthenticationResult')
    if auth_result and 'IdToken' in auth_result:
        return auth_result['IdToken']
    print(auth_result)
    raise ValueError('not authorized')


