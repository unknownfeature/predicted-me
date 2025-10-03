from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_lambda_event_sources as lmes,
    aws_sns_subscriptions as subs)

from shared.variables import Common


def docker_code_asset(build_args: dict[str, str]) -> lmbd.DockerImageCode:
    return lmbd.DockerImageCode.from_image_asset(
        directory=Common.docker_path,
        file=Common.docker_file,
        build_args={Common.lib_dir_arg: Common.lib_dir,
                    Common.backend_dir_arg: Common.backend_dir,
                    Common.shared_path_arg: Common.shared_path,
                    } | build_args
    )

def setup_bedrock_lambda_role(stack, db_stack, role_name):
    role = setup_db_lambda_role(stack, db_stack, role_name)
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

    role.add_to_policy(
        iam.PolicyStatement(
            actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        )
    )

    return role
