from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    RemovalPolicy
)
from constructs import Construct

from .db_stack import PmDbStack
from .text_processing_stack import PmTextStack
from .util import docker_code_asset
from .vpc_stack import PmVpcStack
from shared.variables import Env, Common, Audio


class PmAudioProcessingStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, text_stack: PmTextStack,
                 **kwargs) -> None:
        super().__init__(scope, Audio.stack_name, **kwargs)

        # bucket for transcribe input
        self.transcribe_input_bucket = s3.Bucket(
            self, Audio.transcribe_input_bucket_name,
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        # and for transcribe output
        self.transcribe_output_bucket = s3.Bucket(
            self, Audio.transcribe_output_bucket_name,
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        audio_processor_role = iam.Role(self, Audio.func_transcribe_in_role_name,
                                        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                        managed_policies=[
                                            iam.ManagedPolicy.from_aws_managed_policy_name(
                                                "service-role/AWSLambdaBasicExecutionRole")
                                        ]
                                        )

        audio_processor_role.add_to_policy(iam.PolicyStatement(
            actions=["transcribe:StartTranscriptionJob", "transcribe:GetTranscriptionJob"],
            resources=["*"]
        ))
        self.transcribe_input_bucket.grant_read(audio_processor_role)
        self.transcribe_output_bucket.grant_write(audio_processor_role)

        audio_processor_role.add_to_policy(iam.PolicyStatement(
            actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        ))

        audio_processor_role.add_to_policy(iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=[audio_processor_role.role_arn],
            conditions={
                "StringEquals": {"iam:PassedToService": "transcribe.amazonaws.com"}
            }
        ))
        self.audio_processing_function = lmbd.DockerImageFunction(self, Audio.func_transcribe_in_name,
                                                                  timeout=Audio.func_transcribe_in_timeout,
                                                                  code=docker_code_asset(
                                                                      build_args={
                                                                          Common.func_dir_arg: Audio.func_transcribe_in_code_path,
                                                                      }
                                                                  ),
                                                                  memory_size=Audio.func_transcribe_in_memory_size,
                                                                  role=audio_processor_role,
                                                                  environment={
                                                                      Env.transcribe_bucket_in: self.transcribe_input_bucket.bucket_name,
                                                                      Env.transcribe_bucket_out: self.transcribe_output_bucket.bucket_name,

                                                                  }
                                                                  )

        self.transcribe_input_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.audio_processing_function)
        )

        audio_processed_results_role = iam.Role(self, Audio.func_transcribe_out_role_name,
                                                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                managed_policies=[
                                                    iam.ManagedPolicy.from_aws_managed_policy_name(
                                                        "service-role/AWSLambdaBasicExecutionRole")
                                                ]
                                                )
        audio_processed_results_role.add_to_policy(iam.PolicyStatement(
            actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        ))
        self.transcribe_output_bucket.grant_read(audio_processed_results_role)
        db_stack.db_secret.grant_read(audio_processed_results_role)

        self.transcribe_output_processing_function = lmbd.DockerImageFunction(self, Audio.func_transcribe_out_name,
                                                                              timeout=Audio.func_transcribe_out_timeout,
                                                                              code=docker_code_asset(
                                                                                  build_args={
                                                                                      Common.func_dir_arg: Audio.func_transcribe_out_code_path,
                                                                                      Common.install_mysql_arg: 'True',
                                                                                  }
                                                                              ),
                                                                              memory_size=Audio.func_transcribe_out_memory_size,
                                                                              role=audio_processed_results_role,
                                                                              vpc=vpc_stack.vpc,
                                                                              security_groups=[db_stack.db_sec_group],
                                                                              environment={
                                                                                  Env.transcribe_bucket_out: self.transcribe_output_bucket.bucket_name,
                                                                                  Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                                  Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                                  Env.db_name: db_stack.db_instance.instance_identifier,
                                                                                  Env.text_processing_topic_arn: text_stack.text_processing_topic.topic_arn,
                                                                              })

        self.transcribe_output_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.transcribe_output_processing_function)
        )
