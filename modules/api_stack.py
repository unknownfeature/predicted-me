from aws_cdk import (
    Stack,
    aws_apigatewayv2_alpha as api_gtw,
    aws_apigatewayv2_authorizers_alpha as auth,
    aws_apigatewayv2_integrations_alpha as intgr)
from constructs import Construct

from predictedme.cognito_stack import PmCognitoStack
from predictedme.functions_stack import PmFunctionsStack


class PmApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cognito_stack: PmCognitoStack,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        _name = 'predictedme-api'
        authorizer = 'predictedme-authorizer'

        api_url = 'api.predicted.me'
        self.http_api = api_gtw.HttpApi(self, _name, default_domain_mapping= api_gtw.DomainMappingOptions(
        domain_name=api_gtw.DomainName.from_domain_name_attributes(self, api_url, name=api_url, regional_domain_name='d-ybyz1q7sbk.execute-api.us-east-1.amazonaws.com', regional_hosted_zone_id='Z1UJRXOUMOOFQ8')
    ))
        self.http_authorizer = auth.HttpJwtAuthorizer(id=authorizer,
                                                      identity_source=['$request.header.Authorization'],

                                                      authorizer_name=cognito_stack.app_client.user_pool_client_name,
                                                      jwt_audience=[cognito_stack.app_client.user_pool_client_id],
                                                      jwt_issuer=f'https://cognito-idp.{kwargs.get("env").region}.amazonaws.com/{cognito_stack.user_pool.user_pool_id}',
                                                      )

