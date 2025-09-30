from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_lambda_event_sources as lmes,
    aws_sns_subscriptions as subs)
from constructs import Construct

from .db_stack import PmDbStack
from .util import docker_code_asset
from .vpc_stack import PmVpcStack
from shared.variables import Env, Common, Tagging


class PmTaggingStack(Stack):

    def __init__(self, scope: Construct, db_stack: PmDbStack, vpc_stack: PmVpcStack, **kwargs) -> None:
        super().__init__(scope, Tagging.stack_name, **kwargs)

        self.tagging_topic = sns.Topic(self, Tagging.tagging_topic_name,
                                       display_name=Tagging.tagging_topic_name,
                                       topic_name=Tagging.tagging_topic_name
                                       )

        self.tagging_topic_queue = sqs.Queue(self, Tagging.tagging_queue_name,
                                             queue_name=Tagging.tagging_queue_name,
                                             visibility_timeout=Tagging.tagging_queue_visibility_timeout
                                             )
        self.tagging_topic.add_subscription(
            subs.SqsSubscription(self.tagging_topic_queue)
        )

        tagging_role = iam.Role(
            self, Tagging.tagging_role,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        db_stack.db_secret.grant_read(tagging_role)

        tagging_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        tagging_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        self.tagging_function = lmbd.DockerImageFunction(self, Tagging.tagging_func_name,
                                                         timeout=Tagging.tagging_func_timeout,
                                                         code=docker_code_asset(
                                                             build_args={
                                                                 Common.func_dir_arg: Tagging.tagging_func_code_path,
                                                                 Common.install_mysql_arg: 'True',
                                                             }
                                                         ),
                                                         memory_size=Tagging.tagging_func_memory_size,
                                                         vpc=vpc_stack.vpc,
                                                         role=tagging_role,
                                                         security_groups=[db_stack.db_sec_group],
                                                         environment={
                                                             Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                             Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                             Env.db_name: db_stack.db_instance.instance_identifier,
                                                             Env.generative_model: Tagging.tagging_model_name,

                                                         }
                                                         )

        self.tagging_function.add_event_source(
            lmes.SqsEventSource(self.tagging_topic_queue)
        )
