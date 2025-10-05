import os

from aws_cdk import (
    Stack,
    aws_apigatewayv2_alpha as api_gtw,
    aws_iam as iam,
    aws_lambda as lmbd,
    aws_apigatewayv2_authorizers_alpha as auth)
from constructs import Construct

from shared.variables import Env, Api, Common
from .audio_stack import PmAudioStack
from .cognito_stack import PmCognitoStack
from .db_stack import PmDbStack
from .image_stack import PmImageStack
from .util import ApiFunctionParams, RoleParams, DockerFunctionParams, \
    IntegrationParams, create_and_setup_api_function, on_role_db_callback

#  todo do something with this ugly class
class PmApiStack(Stack):

    def __init__(self, scope: Construct, cognito_stack: PmCognitoStack, image_stack: PmImageStack,
                 audio_stack: PmAudioStack, db_stack: PmDbStack, **kwargs) -> None:
        super().__init__(scope, Api.stack_name, **kwargs)
        self.http_api = api_gtw.HttpApi(self, Api.name, default_domain_mapping=api_gtw.DomainMappingOptions(
            domain_name=api_gtw.DomainName.from_domain_name_attributes(self, Api.api_url, name=Api.api_url,
                                                                       regional_domain_name=os.getenv(
                                                                           Env.regional_domain_name),
                                                                       regional_hosted_zone_id=os.getenv(
                                                                           Env.regional_hosted_zone_id))
        ))

        self.presign_function_role, self.presign_function = self._presign_role_and_function(audio_stack, image_stack)

        self.note_api_function_role,  self.note_api_function = self._note_api_function_and_role(db_stack)

        self.data_api_function_role, self.data_api_function = self._data_api_function_and_role(db_stack)

        self.link_api_function_role, self.link_api_function = self._link_api_function_and_role(db_stack)

        self.schedule_api_function_role, self.schedule_api_function = self._schedule_api_function_and_role(db_stack)

        self.task_api_function_role, self.task_api_function = self._task_api_function_and_role(db_stack)

        self.user_api_function_role, self.user_api_function = self._user_api_function_and_role(db_stack)

        self.tag_api_function_role, self.tag_api_function = self._tag_api_function_and_role(db_stack)

        self.metric_api_function_role, self.metric_api_function = self._metric_api_function_and_role(db_stack)


        self.http_authorizer = auth.HttpJwtAuthorizer(id=Api.authorizer,
                                                      identity_source=['$request.header.Authorization'],

                                                      authorizer_name=cognito_stack.app_client.user_pool_client_name,
                                                      jwt_audience=[cognito_stack.app_client.user_pool_client_id],
                                                      jwt_issuer=f'https://cognito-idp.{kwargs.get("env").region}.amazonaws.com/{cognito_stack.user_pool.user_pool_id}',
                                                      )

    def _presign_role_and_function(self, audio_stack: PmAudioStack, image_stack: PmImageStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.presign_function_name,
            role_params=RoleParams(
                name=Api.presign_function_role_name,
                on_role=lambda role: role.add_to_policy(iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:GetObject"],
                    resources=[image_stack.bda_input_bucket.bucket_arn,
                               f"{image_stack.bda_input_bucket.bucket_arn.bucket_arn}/*",
                               audio_stack.transcribe_input_bucket.bucket_arn,
                               f"{audio_stack.transcribe_input_bucket.bucket_arn.bucket_arn}/*"]
                ))
            ),
            func_params=DockerFunctionParams(
                timeout=Api.presign_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.presign_function_code_path,
                },
                environment={

                    Env.bda_input_bucket_name: image_stack.bda_input_bucket.bucket_name,
                    Env.transcribe_bucket_in: audio_stack.transcribe_input_bucket.bucket_name,

                }
            ),
            integration_params=IntegrationParams(
                url_path=Api.presign_function_url_path,
                methods=Api.presign_function_methods,
                name=Api.presign_function_integration_name
            )
        )
        return create_and_setup_api_function(self, params, self.http_api)

    def _note_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.note_api_function_name,
            role_params=RoleParams(
                name=Api.note_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.note_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.note_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.note_api_function_url_path,
                methods=Api.note_api_function_methods,
                name=Api.note_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _data_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.data_api_function_name,
            role_params=RoleParams(
                name=Api.data_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.data_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.data_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.data_api_function_url_path,
                methods=Api.data_api_function_methods,
                name=Api.data_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _link_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.link_api_function_name,
            role_params=RoleParams(
                name=Api.link_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.link_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.link_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.link_api_function_url_path,
                methods=Api.link_api_function_methods,
                name=Api.link_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _schedule_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.data_schedule_api_function_name,
            role_params=RoleParams(
                name=Api.data_schedule_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.data_schedule_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.data_schedule_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.data_schedule_api_function_url_path,
                methods=Api.data_schedule_api_function_methods,
                name=Api.data_schedule_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _task_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.task_api_function_name,
            role_params=RoleParams(
                name=Api.task_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.task_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.task_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.task_api_function_url_path,
                methods=Api.task_api_function_methods,
                name=Api.task_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _user_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.user_api_function_name,
            role_params=RoleParams(
                name=Api.user_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.user_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.user_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.user_api_function_url_path,
                methods=Api.user_api_function_methods,
                name=Api.user_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _tag_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.tag_api_function_name,
            role_params=RoleParams(
                name=Api.tag_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.tag_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.tag_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.tag_api_function_url_path,
                methods=Api.tag_api_function_methods,
                name=Api.tag_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)

    def _metric_api_function_and_role(self, db_stack: PmDbStack) -> (iam.Role, lmbd.Function):
        params = ApiFunctionParams(
            func_name=Api.metric_api_function_name,
            role_params=RoleParams(
                name=Api.metric_api_function_role_name,
                on_role=on_role_db_callback(db_stack),
            ),
            func_params=DockerFunctionParams(
                timeout=Api.metric_api_function_timeout,
                build_args={
                    Common.func_dir_arg: Api.metric_api_function_code_path,
                    Common.install_mysql_arg: 'True',
                },
                environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,

                },
                on_created=lambda function: db_stack.db_instance.connections.allow_default_port_from(function)
            ),
            integration_params=IntegrationParams(
                url_path=Api.metric_api_function_url_path,
                methods=Api.metric_api_function_methods,
                name=Api.metric_api_function_integration_name
            )
        )

        return create_and_setup_api_function(self, params, self.http_api)
    