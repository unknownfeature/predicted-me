import json
import os

from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_s3 as s3,
    aws_sqs as sqs,
    RemovalPolicy, aws_lambda as lmbd,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    aws_sns_subscriptions as subs,
    aws_bedrock as bedrock)
from constructs import Construct

from modules.db_stack import PmDbStack
from modules.vpc_stack import PmVpcStack
from modules.constants import *


class PmTextStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack,
                 **kwargs) -> None:
        super().__init__(scope, Text.stack_name, **kwargs)

        self.text_processing_topic = sns.Topic(self, Text.text_topic_name,
                                               display_name=Text.text_topic_name,
                                               topic_name=Text.text_topic_name
                                               )


        self.text_processing_queue = sqs.Queue(self, Text.text_queue_name,
                                               queue_name=Text.text_queue_name,
                                               visibility_timeout=Text.text_queue_visibility_timeout
                                               )

        self.text_processing_topic.add_subscription(
            subs.SqsSubscription(self.text_processing_queue)
        )

        text_processor_role = iam.Role(
            self, Text.text_processor_role,
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

        self.text_processing_function = lmbd.DockerImageFunction(self, Text.func_bda_in_name,
                                                             timeout=Text.text_processing_func_timeout,
                                                             code=lmbd.DockerImageCode.from_image_asset(
                                                                 directory=os.path.join(functions_root,
                                                                                        Text.text_processing_func_code_path),
                                                                 file='Dockerfile'
                                                             ),
                                                             memory_size=Text.text_processing_func_memory_size,
                                                             vpc=vpc_stack.vpc,
                                                                 role=self.text_processor_role,
                                                                 security_groups=[db_stack.db_sec_group],
                                                             environment={
                                                                 'DB_SECRET_ARN': db_stack.db_secret.secret_full_arn,
                                                                 'DB_ENDPOINT': db_stack.db_instance.db_instance_endpoint_address,
                                                                 'DB_NAME': db_stack.db_instance.instance_identifier,


                                                                 'TEXT_PROCESSING_QUEUE_URL': self.text_processing_queue.queue_url
                                                             }
                                                             )



        self.text_processing_function.add_event_source(
            lmbd.SqsEventSource(self.text_processing_queue)
        )


