from typing import Dict

from infra.pm.db_stack import PmDbStack
from aws_cdk import (
    Stack,
    aws_s3 as s3, RemovalPolicy

from infra.pm.function_factories import FunctionFactoryParams
from shared.variables import Common

aws_iam as iam)
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda as lmbd, )

from infra.pm.db_stack import PmDbStack


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


def docker_code_asset(build_args: Dict[str, str]) -> lmbd.DockerImageCode:
    return lmbd.DockerImageCode.from_image_asset(
        directory=Common.docker_path,
        file=Common.docker_file,
        build_args={Common.lib_dir_arg: Common.lib_dir,
                    Common.backend_dir_arg: Common.backend_dir,
                    Common.shared_path_arg: Common.shared_path,
                    } | build_args
    )


def create_function(stack: Stack, params: FunctionFactoryParams):
    role = params.role_supplier(params.function_params)

    function = lmbd.DockerImageFunction(stack, params.function_params.name,
                                        function_name=params.function_params.name,
                                        timeout=params.function_params.timeout,
                                        code=docker_code_asset(
                                            build_args=params.build_args,
                                        ),
                                        vpc=params.vpc,
                                        role=role,
                                        environment=params.environment,
                                        )

    if params.and_then:
        params.and_then(function)

    return role, function


def create_bucket(stack: Stack, name: str)
    return s3.Bucket(
        stack, name,
        removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL
    )
