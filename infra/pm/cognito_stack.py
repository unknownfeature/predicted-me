import os

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_secretsmanager as secretsmanager,
    aws_cognito as cognito)
from constructs import Construct

from infra.pm.function_factories import FunctionFactoryParams, create_function_role_factory, \
    custom_resource_trigger_cb_factory
from infra.pm.util import create_function
from shared.variables import *
from .input import Cognito, Common


class PmCognitoStack(Stack):

    def __init__(self, scope: Construct, **kwargs) -> None:
        super().__init__(scope, Cognito.stack_name, **kwargs)

        self.user_pool = cognito.UserPool(self, Cognito.pool_name,
                                          user_pool_name=Cognito.pool_name,
                                          sign_in_aliases=cognito.SignInAliases(
                                              email=True
                                          ),
                                          self_sign_up_enabled=True,
                                          auto_verify=cognito.AutoVerifiedAttrs(
                                              email=True
                                          ),
                                          user_verification=cognito.UserVerificationConfig(
                                              email_subject=Cognito.ver_email_subj,
                                              email_body=Cognito.ver_email_body,
                                              email_style=cognito.VerificationEmailStyle.CODE
                                          ),
                                          password_policy=cognito.PasswordPolicy(
                                              min_length=8,
                                              require_lowercase=True,
                                              require_uppercase=True,
                                              require_digits=True,
                                              require_symbols=True,
                                              password_history_size=5
                                          ),
                                          account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
                                          removal_policy=RemovalPolicy.DESTROY
                                          )

        self.app_client = self.user_pool.add_client(
            Cognito.client,
            user_pool_client_name=Cognito.client,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            )
        )
        self.admin_password_secret = secretsmanager.Secret(self, Cognito.admin_secret_name,
                                                           generate_secret_string=secretsmanager.SecretStringGenerator(
                                                               password_length=16,
                                                               exclude_characters='\'@/\\ '
                                                           )
                                                           )

        self.tmp_admin_password_secret = secretsmanager.Secret(self, Cognito.admin_tmp_secret_name,
                                                               generate_secret_string=secretsmanager.SecretStringGenerator(
                                                                   password_length=16,
                                                                   exclude_characters='\'@/\\ '
                                                               )
                                                               )

        def on_role(role):
            self.admin_password_secret.grant_read(role)
            self.tmp_admin_password_secret.grant_read(role)
            self.user_pool.grant(role, 'cognito-idp:AdminCreateUser')
            self.user_pool.grant(role, 'cognito-idp:AdminSetUserPassword')

        self.admin_creator_lambda = create_function(self, FunctionFactoryParams(
            function_params=Cognito.admin_user_creator_function,
            build_args={
                Common.func_dir_arg: Cognito.admin_user_creator_function.code_path,
            },
            environment={
                cognito_pool_id: self.user_pool.user_pool_id,
                admin_secret_arn: self.admin_password_secret.secret_arn,
                admin_tmp_secret_arn: self.tmp_admin_password_secret.secret_arn,
                admin_user: os.getenv(admin_user),

            },
            role_supplier=create_function_role_factory(on_role),
            and_then=custom_resource_trigger_cb_factory(
                self,
                properties={},
                custom_resource_triggered_function=Cognito.admin_user_creator_function
            )
        ))
