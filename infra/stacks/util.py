from typing import Dict, Sequence, Callable

from aws_cdk import (
    Stack,
    aws_lambda as lmbd,
    aws_apigatewayv2 as api_gtw,
    aws_iam as iam, Duration)
from aws_cdk.aws_iam import PolicyStatement

from infra.stacks.db_stack import PmDbStack
from shared.variables import Common


class RoleParams:
    def __init__(self, name: str, on_role: Callable[[iam.Role], None]):
        self.name = name
        self.on_role = on_role


class DockerFunctionParams:
    def __init__(self, timeout: Duration , build_args: Dict[str, str], environment: Dict[str, str], on_created: Callable[[lmbd.Function], None] = None):
        self.timeout = timeout
        self.build_args = build_args
        self.environment = environment
        self.on_created = on_created


class IntegrationParams:
    def __init__(self, url_path: str, methods: Sequence[api_gtw.HttpMethod], name: str):
        self.url_path = url_path
        self.methods = methods
        self.name = name


class ApiFunctionParams:
    def __init__(self,  func_name: str, role_params: RoleParams, func_params: DockerFunctionParams,
                 integration_params: IntegrationParams):
        self.func_name = func_name
        self.role_params = role_params
        self.func_params = func_params
        self.integration_params = integration_params


def docker_code_asset(build_args: Dict[str, str]) -> lmbd.DockerImageCode:
    return lmbd.DockerImageCode.from_image_asset(
        directory=Common.docker_path,
        file=Common.docker_file,
        build_args={Common.lib_dir_arg: Common.lib_dir,
                    Common.backend_dir_arg: Common.backend_dir,
                    Common.shared_path_arg: Common.shared_path,
                    } | build_args
    )


def setup_bedrock_lambda_role(stack: Stack, db_stack: PmDbStack, role_name: str):
    role = create_lambda_with_db_role(stack, db_stack, role_name)
    role.add_to_policy(
        iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        )
    )
    return role


def setup_db_lambda_role(stack, db_stack, role_name):
    role = iam.Role(
        stack, role_name,
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        ]
    )
    db_stack.db_secret.grant_read(role)


def create_and_setup_api_function(stack: Stack, params: ApiFunctionParams, api: api_gtw.HttpApi) -> (iam.Role, lmbd.Function):
    role = create_lambda_role(stack, params.role_params.name,
                              params.role_params.on_role if params.role_params.on_role else lambda _: None)

    function = lmbd.DockerImageFunction(stack, params.func_name,
                                        function_name=params.func_name,
                                        timeout=params.func_params.timeout,
                                        code=docker_code_asset(
                                            build_args=params.func_params.build_args,
                                        ),
                                        role=role,
                                        environment=params.func_params.environment,
                                        )

    if params.func_params.on_created:
        params.func_params.on_created(function)

    api.add_routes(path=params.integration_params.url_path,
                   methods=params.integration_params.methods,
                   integration=api_gtw.HttpLambdaIntegration(params.integration_params.name, function))
    return role, function


on_role_db_callback = lambda db_stack: lambda role: db_stack.db_secret.grant_read(role)

def create_lambda_with_db_role(stack: Stack, db_stack: PmDbStack, role_name: str):
    return create_lambda_role(stack, role_name, on_role_db_callback(db_stack))


def create_lambda_role(stack: Stack, role_name: str, on_created=lambda role: None):
    role = iam.Role(
        stack, role_name,
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        ]
    )

    role.add_to_policy(
        iam.PolicyStatement(
            actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        )
    )
    on_created(role)
    return role


def create_lambda_role_with_policies(stack: Stack, role_name: str, policy_statements: Sequence[PolicyStatement]):
    def on_created(role):
        for ps in policy_statements:
            role.add_to_policy(ps)

    return create_lambda_role(stack, role_name, on_created)
