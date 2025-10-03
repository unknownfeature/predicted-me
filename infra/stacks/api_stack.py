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
from .util import docker_code_asset, setup_db_lambda_role

# todo refacror
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


        #  presign
        self.presign_function_role = iam.Role(self, Api.presign_function_role_name,
                                              assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                              managed_policies=[
                                                  iam.ManagedPolicy.from_aws_managed_policy_name(
                                                      "service-role/AWSLambdaBasicExecutionRole")
                                              ]
                                              )
        self.presign_function_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:PutObject", "s3:GetObject"],
            resources=[image_stack.bda_input_bucket.bucket_arn,
                       f"{image_stack.bda_input_bucket.bucket_arn.bucket_arn}/*",
                       audio_stack.transcribe_input_bucket.bucket_arn,
                       f"{audio_stack.transcribe_input_bucket.bucket_arn.bucket_arn}/*"]
        ))

        self.presign_function = lmbd.DockerImageFunction(self, Api.presign_function_name,
                                                         function_name=Api.presign_function_name,
                                                         timeout=Api.presign_function_timeout,
                                                         code=docker_code_asset(
                                                             build_args={
                                                                 Common.func_dir_arg: Api.presign_function_code_path,
                                                             }
                                                         ),
                                                         role=self.presign_function_role,
                                                         environment={

                                                             Env.bda_input_bucket_name: image_stack.bda_input_bucket.bucket_name,
                                                             Env.transcribe_bucket_in: audio_stack.transcribe_input_bucket.bucket_name,

                                                         }
                                                         )

        self.http_api.add_routes(path=Api.presign_function_url_path, methods=Api.presign_function_methods,
                                 integration=api_gtw.HttpLambdaIntegration(Api.presign_function_integration,
                                                                           self.presign_function, ))

        #  note
        self.note_api_function_role = setup_db_lambda_role(self, db_stack, Api.note_api_function_methods)

        self.note_api_function = lmbd.DockerImageFunction(self, Api.note_api_function_name,
                                                          function_name=Api.note_api_function_name,
                                                          timeout=Api.note_api_function_timeout,
                                                          code=docker_code_asset(
                                                              build_args={
                                                                  Common.func_dir_arg: Api.note_api_function_code_path,
                                                                  Common.install_mysql_arg: 'True',
                                                              }
                                                          ),
                                                          role=self.note_api_function_role,
                                                          environment={
                                                              Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                              Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                              Env.db_name: db_stack.db_instance.instance_identifier,

                                                          }
                                                          )
        
        db_stack.db_instance.connections.allow_default_port_from(self.note_api_function)
        
        self.http_api.add_routes(path=Api.note_api_function_url_path,
                                 methods=Api.note_api_function_methods,
                                 integration=api_gtw.HttpLambdaIntegration(Api.note_api_function_integration,
                                                                           self.note_api_function, ))

        #  data
        self.data_api_function_role = setup_db_lambda_role(self, db_stack, Api.data_api_function_methods)

        self.data_api_function = lmbd.DockerImageFunction(self, Api.data_api_function_name,
                                                          function_name=Api.data_api_function_name,
                                                          timeout=Api.data_api_function_timeout,
                                                          code=docker_code_asset(
                                                              build_args={
                                                                  Common.func_dir_arg: Api.data_api_function_code_path,
                                                                  Common.install_mysql_arg: 'True',
                                                              }
                                                          ),
                                                          role=self.data_api_function_role,
                                                          environment={
                                                              Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                              Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                              Env.db_name: db_stack.db_instance.instance_identifier,

                                                          }
                                                          )

        db_stack.db_instance.connections.allow_default_port_from(self.data_api_function)

        self.http_api.add_routes(path=Api.data_api_function_url_path,
                                 methods=Api.data_api_function_url_path,
                                 integration=api_gtw.HttpLambdaIntegration(Api.data_api_function_integration,
                                                                           self.data_api_function, ))

        #  link
        self.link_api_function_role = setup_db_lambda_role(self, db_stack, Api.link_api_function_methods)

        self.link_api_function = lmbd.DockerImageFunction(self, Api.link_api_function_name,
                                                          function_name=Api.link_api_function_name,
                                                          timeout=Api.link_api_function_timeout,
                                                          code=docker_code_asset(
                                                              build_args={
                                                                  Common.func_dir_arg: Api.link_api_function_code_path,
                                                                  Common.install_mysql_arg: 'True',
                                                              }
                                                          ),
                                                          role=self.link_api_function_role,
                                                          environment={
                                                              Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                              Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                              Env.db_name: db_stack.db_instance.instance_identifier,

                                                          }
                                                          )

        db_stack.db_instance.connections.allow_default_port_from(self.link_api_function)
        self.http_api.add_routes(path=Api.link_api_function_url_path,
                                 methods=Api.link_api_function_methods,
                                 integration=api_gtw.HttpLambdaIntegration(Api.link_api_function_integration,
                                                                           self.link_api_function, ))

        #  schedule
        self.schedule_api_function_role = setup_db_lambda_role(self, db_stack, Api.schedule_api_function_methods)

        self.schedule_api_function = lmbd.DockerImageFunction(self, Api.schedule_api_function_name,
                                                          function_name=Api.schedule_api_function_name,
                                                          timeout=Api.schedule_api_function_timeout,
                                                          code=docker_code_asset(
                                                              build_args={
                                                                  Common.func_dir_arg: Api.schedule_api_function_code_path,
                                                                  Common.install_mysql_arg: 'True',
                                                              }
                                                          ),
                                                          role=self.schedule_api_function_role,
                                                          environment={
                                                              Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                              Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                              Env.db_name: db_stack.db_instance.instance_identifier,

                                                          }
                                                          )

        db_stack.db_instance.connections.allow_default_port_from(self.schedule_api_function)
        self.http_api.add_routes(path=Api.schedule_api_function_url_path,
                                 methods=Api.schedule_api_function_methods,
                                 integration=api_gtw.HttpLambdaIntegration(Api.schedule_api_function_integration,
                                                                           self.schedule_api_function, ))

        #  task
        self.task_api_function_role = setup_db_lambda_role(self, db_stack, Api.task_api_function_methods)

        self.task_api_function = lmbd.DockerImageFunction(self, Api.task_api_function_name,
                                                          function_name=Api.task_api_function_name,
                                                          timeout=Api.task_api_function_timeout,
                                                          code=docker_code_asset(
                                                              build_args={
                                                                  Common.func_dir_arg: Api.task_api_function_code_path,
                                                                  Common.install_mysql_arg: 'True',
                                                              }
                                                          ),
                                                          role=self.task_api_function_role,
                                                          environment={
                                                              Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                              Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                              Env.db_name: db_stack.db_instance.instance_identifier,

                                                          }
                                                          )

        db_stack.db_instance.connections.allow_default_port_from(self.task_api_function)
        self.http_api.add_routes(path=Api.task_api_function_url_path,
                                 methods=Api.task_api_function_methods,
                                 integration=api_gtw.HttpLambdaIntegration(Api.task_api_function_integration,
                                                                           self.task_api_function, ))
        
        
        #  user
        self.user_api_function_role = setup_db_lambda_role(self, db_stack, Api.user_api_function_methods)

        self.user_api_function = lmbd.DockerImageFunction(self, Api.user_api_function_name,
                                                          function_name=Api.user_api_function_name,
                                                          timeout=Api.user_api_function_timeout,
                                                          code=docker_code_asset(
                                                              build_args={
                                                                  Common.func_dir_arg: Api.user_api_function_code_path,
                                                                  Common.install_mysql_arg: 'True',
                                                              }
                                                          ),
                                                          role=self.user_api_function_role,
                                                          environment={
                                                              Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                              Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                              Env.db_name: db_stack.db_instance.instance_identifier,

                                                          }
                                                          )

        db_stack.db_instance.connections.allow_default_port_from(self.user_api_function)
        self.http_api.add_routes(path=Api.user_api_function_url_path,
                                 methods=Api.user_api_function_methods,
                                 integration=api_gtw.HttpLambdaIntegration(Api.user_api_function_integration,
                                                                           self.user_api_function, ))

        self.http_authorizer = auth.HttpJwtAuthorizer(id=Api.authorizer,
                                                      identity_source=['$request.header.Authorization'],

                                                      authorizer_name=cognito_stack.app_client.user_pool_client_name,
                                                      jwt_audience=[cognito_stack.app_client.user_pool_client_id],
                                                      jwt_issuer=f'https://cognito-idp.{kwargs.get("env").region}.amazonaws.com/{cognito_stack.user_pool.user_pool_id}',
                                                      )
