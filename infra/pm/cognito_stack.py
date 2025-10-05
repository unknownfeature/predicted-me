from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_cognito as cognito)
from constructs import Construct

from shared.variables import Cognito


class PmCognitoStack(Stack):

    def __init__(self, scope: Construct,  **kwargs) -> None:
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
                                                 require_symbols=True
                                             ),
                                          account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
                                          removal_policy=RemovalPolicy.DESTROY
                                          )

        self.app_client = self.user_pool.add_client(
            Cognito.client,
            user_pool_client_name=Cognito.client,
            auth_flows=cognito.AuthFlow(
                user_password=True
            )
        )


