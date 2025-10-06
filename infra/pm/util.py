from typing import Dict

from aws_cdk import (
    Stack,
    aws_lambda as lmbd, )
from aws_cdk import (
    aws_s3 as s3, RemovalPolicy,
    aws_sqs as aws_sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    Duration)

from backend.lib.func import sqs
from infra.pm.function_factories import FunctionFactoryParams
from shared.variables import Common


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
    role = params.role_supplier(stack, params.function_params)

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


def create_bucket(stack: Stack, name: str) -> s3.Bucket:
    return s3.Bucket(
        stack, name,
        removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL
    )


def create_queue(stack: Stack, name: str, visibility_timeout: Duration, with_subscription_to: sns.Topic) -> aws_sqs.Queue:
    queue =  aws_sqs.Queue(stack, name, queue_name=name, visibility_timeout=visibility_timeout)
    if with_subscription_to:
        with_subscription_to.add_subscription(subs.SqsSubscription(queue))
    return queue


