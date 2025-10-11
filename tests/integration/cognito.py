import boto3


def login(email, password, user_pool_id, client_id):
    cognito_client = boto3.client("cognito-idp")

    cognito_client.sign_up(
        ClientId=client_id,
        Username=email,
        Password=password,
        UserAttributes=[{'Name': 'email', 'Value': email}]
    )

    cognito_client.admin_confirm_sign_up(
        UserPoolId=user_pool_id,
        Username=email
    )

    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': email,
            'PASSWORD': password
        }
    )

    return auth_response.get('AuthenticationResult')

