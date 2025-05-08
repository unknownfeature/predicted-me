import os

from aws_cdk import (
    Stack,
    aws_apigatewayv2_alpha as api_gtw,
    aws_apigatewayv2_authorizers_alpha as auth)
from constructs import Construct
from modules.cognito_stack import PmCognitoStack
from modules.constants import *

class PmApiStack(Stack):

    def __init__(self, scope: Construct, cognito_stack: PmCognitoStack,**kwargs) -> None:
        super().__init__(scope, Api.stack_name, **kwargs)


        self.http_api = api_gtw.HttpApi(self, Api.name, default_domain_mapping= api_gtw.DomainMappingOptions(
        domain_name=api_gtw.DomainName.from_domain_name_attributes(self, Api.api_url, name=Api.api_url, regional_domain_name=os.getenv(regional_domain_name), regional_hosted_zone_id=os.getenv(regional_hosted_zone_id))
    ))
        self.http_authorizer = auth.HttpJwtAuthorizer(id=Api.authorizer,
                                                      identity_source=['$request.header.Authorization'],

                                                      authorizer_name=cognito_stack.app_client.user_pool_client_name,
                                                      jwt_audience=[cognito_stack.app_client.user_pool_client_id],
                                                      jwt_issuer=f'https://cognito-idp.{kwargs.get("env").region}.amazonaws.com/{cognito_stack.user_pool.user_pool_id}',
                                                      )

