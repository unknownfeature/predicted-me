import os

from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_lambda_event_sources as lmes,
    aws_sns_subscriptions as subs)
from constructs import Construct
from shared.variables import Env, Common, Text
from .db_stack import PmDbStack
from .vpc_stack import PmVpcStack
from .tagging_stack import PmTaggingStack
from .util import docker_code_asset

class PmTextStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, tagging_stack: PmTaggingStack,
                 **kwargs) -> None:
        super().__init__(scope, Text.stack_name, **kwargs)

        self.text_processing_topic = sns.Topic(self, Text.text_topic_name,
                                               display_name=Text.text_topic_name,
                                               topic_name=Text.text_topic_name
                                               )


        self.text_processing_queue = sqs.Queue(self, Text.metrics_extraction_queue_name,
                                               queue_name=Text.metrics_extraction_queue_name,
                                               visibility_timeout=Text.metrics_extraction_queue_visibility_timeout
                                               )

        self.text_processing_topic.add_subscription(
            subs.SqsSubscription(self.text_processing_queue)
        )

        text_processor_role = iam.Role(
            self, Text.metrics_extraction_role,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        db_stack.db_secret.grant_read(text_processor_role)

        text_processor_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        text_processor_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        self.text_processing_function = lmbd.DockerImageFunction(self, Text.metrics_extraction_func_name,
                                                                 timeout=Text.metrics_extraction_func_timeout,
                                                                 code=docker_code_asset(
                                                                        build_args={
                                                                            Common.func_dir_arg: Text.metrics_extraction_func_code_path,
                                                                            Common.install_mysql_arg: 'True',
                                                                        }
                                                                    ),
                                                                 memory_size=Text.metrics_extraction_func_memory_size,
                                                                 vpc=vpc_stack.vpc,
                                                                 role=text_processor_role,
                                                                 security_groups=[db_stack.db_sec_group],

                                                                 environment={
                                                                     Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                     Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                     Env.db_name: db_stack.db_instance.instance_identifier,
                                                                     Env.generative_model: Text.text_processing_model,
                                                                     Env.tagging_topic_arn: tagging_stack.tagging_topic.topic_arn,

                                                                 }
                                                                 )



        self.text_processing_function.add_event_source(
            lmes.SqsEventSource(self.text_processing_queue)
        )


