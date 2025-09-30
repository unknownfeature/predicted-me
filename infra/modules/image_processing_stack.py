import json
import os

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy, aws_lambda as lmbd,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    aws_bedrock as bedrock)
from constructs import Construct

from modules.db_stack import PmDbStack
from modules.vpc_stack import PmVpcStack
from shared.constants import *
from modules.text_processing_stack import PmTextStack

class PmImageProcessingStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, text_stack: PmTextStack,
                 **kwargs) -> None:
        super().__init__(scope, Image.stack_name, **kwargs)

        # pre setup blueprint for BDA
        blueprint_schema = {
            "class": "ImageDescription",
            "description": "The user wants a concise, detailed, and objective summary of the image content for cataloging purposes. And relevant image text extraction where possible.",
            "inference_schema": {
                "type": "object",
                "properties": {
                    "image_description": {
                        "type": "string",
                        "description": "A single, detailed paragraph describing the image's main subject, scene, colors, lighting, and any obvious actions.",
                        "inference_type": "GENERATIVE_FIELD"
                    },
                    "image_text": {
                        "type": "string",
                        "description": "Extract relevant text from the image",
                        "inference_type": "GENERATIVE_FIELD"
                    }
                },
                "required": ["image_description", "image_text"]
            }
        }

        image_blueprint = bedrock.CfnBlueprint(
            self, Image.bda_blueprint_name,
            blueprint_name=Image.bda_blueprint_name,
            schema=blueprint_schema,
            type="IMAGE"
        )

        # create buckets for images
        self.bda_input_bucket = s3.Bucket(
            self, Image.images_bucket_name,
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        # and for BDA output
        self.bda_output_bucket = s3.Bucket(
            self, Image.bda_output_bucket_name,
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # configure access for BDA
        bda_role = iam.Role(
            self, Image.bda_role_name,
            assumed_by=iam.ServicePrincipal("data-automation.bedrock.amazonaws.com")
        )

        bda_role.add_to_policy(
            iam.PolicyStatement(
                actions=['bedrock:InvokeModel'],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        self.bda_input_bucket.grant_read(bda_role)
        self.bda_output_bucket.grant_write(bda_role)

        lambda_role = iam.Role(
            self, Image.func_bda_in_role_name,
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
            ]
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=['bedrock-data-automation:StartDataAutomationJob'],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        self.image_processing_function = lmbd.DockerImageFunction(self, Image.func_bda_in_name,
                                                                  timeout=Image.func_bda_in_timeout,
                                                                  code=lmbd.DockerImageCode.from_image_asset(
                                                                      directory=os.path.join(functions_root,
                                                                                             Image.func_bda_in_code_path),
                                                                      file='Dockerfile'),
                                                                  memory_size=Image.func_bda_in_memory_size,
                                                                  environment={
                                                                      'OUTPUT_BUCKET_NAME': self.bda_output_bucket.bucket_name,
                                                                      'JOB_EXECUTION_ROLE_ARN': bda_role.role_arn,
                                                                      'BLUEPRINT_NAME': image_blueprint.blueprint_name,
                                                                      'BDA_MODEL_NAME': Image.bda_model_name
                                                                  })

        # setup role for BDA output processing lambda

        db_writer_role = iam.Role(
            self, Image.func_bda_out_role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # grant readfrom output bucket
        self.bda_output_bucket.grant_read(db_writer_role)

        # allow read DN secret
        db_stack.db_secret.grant_read(db_writer_role)
        # and create ENI to connect to DB
        db_writer_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        self.bda_out_processing_function = lmbd.DockerImageFunction(self, Image.func_bda_out_name,
                                                                    timeout=Image.func_bda_out_timeout,
                                                                    code=lmbd.DockerImageCode.from_image_asset(
                                                                        directory=os.path.join(functions_root,
                                                                                               Image.func_bda_out_code_path),
                                                                        file='Dockerfile'),
                                                                    memory_size=Image.func_bda_out_memory_size,
                                                                    vpc=vpc_stack.vpc,
                                                                    security_groups=[db_stack.db_sec_group],
                                                                    environment={
                                                                        'DB_SECRET_ARN': db_stack.db_secret.secret_full_arn,
                                                                        'DB_ENDPOINT': db_stack.db_instance.db_instance_endpoint_address,
                                                                        'DB_NAME': db_stack.db_instance.instance_identifier,
                                                                        'SNS_TOPIC_ARN':  text_stack.text_processing_topic.topic_arn
                                                                    })

        # and setup the trigger
        self.bda_output_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.bda_out_processing_function),
            s3.NotificationKeyFilter(suffix=".jsonl")
        )

        text_stack.text_processing_topic.grant_publish(self.bda_out_processing_function)
