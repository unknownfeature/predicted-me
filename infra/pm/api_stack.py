import os
from typing import Dict

from aws_cdk import (
    Stack,
    aws_apigatewayv2 as api_gtw,
    aws_lambda as lmbd,
    aws_apigatewayv2_authorizers as auth)

from constructs import Construct
from shared.variables import Env, Api, Common, ApiFunction
from .audio_stack import PmAudioStack
from .cognito_stack import PmCognitoStack
from .db_stack import PmDbStack
from .function_factories import http_api_integration_cb_factory, create_function_role_factory, FunctionFactoryParams, create_role_with_db_access_factory, function_with_db_access_cb_factory
from .image_stack import PmImageStack
from .constants import true
from .util import create_function
from .text_stack import PmTextStack
from .vpc_stack import PmVpcStack


class PmApiStack(Stack):

    def __init__(self, scope: Construct, cognito_stack: PmCognitoStack, image_stack: PmImageStack,
                 audio_stack: PmAudioStack, text_stack: PmTextStack,  db_stack: PmDbStack, vpc_stack: PmVpcStack, **kwargs):
        super().__init__(scope, Api.stack_name, **kwargs)

        self.http_api = api_gtw.HttpApi(self, Api.name, default_domain_mapping=api_gtw.DomainMappingOptions(
            domain_name=api_gtw.DomainName.from_domain_name_attributes(self, Api.api_url, name=Api.api_url,
                                                                       regional_domain_name=os.getenv(
                                                                           Env.regional_domain_name),
                                                                       regional_hosted_zone_id=os.getenv(
                                                                           Env.regional_hosted_zone_id))
        ))

        jwt_issuer = f'https://cognito-idp.{kwargs.get("env").region}.amazonaws.com/{cognito_stack.user_pool.user_pool_id}'

        self.http_authorizer = auth.HttpJwtAuthorizer(id=Api.authorizer,
                                                      identity_source=['$request.header.Authorization'],
                                                      authorizer_name=cognito_stack.app_client.user_pool_client_name,
                                                      jwt_audience=[cognito_stack.app_client.user_pool_client_id],
                                                      jwt_issuer=jwt_issuer)

        self.presign_function = self._presign(audio_stack, image_stack, vpc_stack)

        self.note_api_function = create_function(self,
                                                 self._create_api_function_with_db_params(db_stack, vpc_stack, Api.note,
                                                                                          {Env.text_processing_topic_arn: text_stack.text_processing_topic.topic_arn}))

        self.data_api_function = create_function(self, self._create_api_function_with_db_params(db_stack, vpc_stack, Api.data))

        self.link_api_function = create_function(self, self._create_api_function_with_db_params(db_stack, vpc_stack, Api.link))

        self.data_schedule_api_function = create_function(self,
                                                          self._create_api_function_with_db_params(db_stack, vpc_stack, Api.data_schedule))

        self.occurrence_schedule_api_function = create_function(self,
                                                                self._create_api_function_with_db_params(db_stack, vpc_stack, Api.occurrence_schedule))

        self.task_api_function = create_function(self,
                                                 self._create_api_function_with_db_params(db_stack, vpc_stack,Api.task))

        self.user_api_function = create_function(self,
                                                 self._create_api_function_with_db_params(db_stack, vpc_stack, Api.user))

        self.metric_api_function = create_function(self,
                                                   self._create_api_function_with_db_params(db_stack, vpc_stack, Api.metric))

        self.tag_api_function = create_function(self,
                                                self._create_api_function_with_db_params(db_stack, vpc_stack, Api.tag))

    def _presign(self, audio_stack: PmAudioStack, image_stack: PmImageStack, vpc_stack: PmVpcStack) -> lmbd.Function:
        def on_role(role):
            image_stack.bda_input_bucket.grant_read(role)
            image_stack.bda_input_bucket.grant_write(role)
            audio_stack.transcribe_input_bucket.grant_read(role)
            audio_stack.transcribe_input_bucket.grant_write(role)

        params = FunctionFactoryParams(function_params=Api.presign, build_args={
            Common.func_dir_arg: Api.presign.code_path,
        }, environment={

            Env.bda_input_bucket_name: image_stack.bda_input_bucket.bucket_name,
            Env.transcribe_bucket_in: audio_stack.transcribe_input_bucket.bucket_name,

        }, role_supplier=create_function_role_factory(on_role),
                                       and_then=http_api_integration_cb_factory(self.http_api, Api.presign),
                                       vpc=vpc_stack.vpc)

        return create_function(self, params)

    def _create_api_function_with_db_params(self, db_stack: PmDbStack, vpc_stack: PmVpcStack,
                                            function_params: ApiFunction, env_override: Dict[str, str] = None) -> FunctionFactoryParams:
        return FunctionFactoryParams(
            function_params=function_params,
            build_args={
                Common.func_dir_arg: function_params.code_path,
                Common.install_mysql_arg: true,
            },
            environment={
                Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                Env.db_name: db_stack.db_instance.instance_identifier,
                Env.db_port: db_stack.db_instance.db_instance_endpoint_port,
            } | env_override if env_override is not None else {},
            role_supplier=create_role_with_db_access_factory(db_stack.db_secret),
            and_then=function_with_db_access_cb_factory(db_stack.db_instance,
                                                        http_api_integration_cb_factory(self.http_api,
                                                                                        function_params), ),
            vpc=vpc_stack.vpc,
        )
