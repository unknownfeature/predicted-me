import os
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    Duration, RemovalPolicy
)
from constructs import Construct

from modules.db_stack import PmDbStack
from modules.vpc_stack import PmVpcStack

from modules.text_processing_stack import PmTextStack


class PmAudioProcessingStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack,  text_stack: PmTextStack, **kwargs) -> None:
        super().__init__(scope, "PmAudioProcessingStack", **kwargs)

        # bucket for transcribe input
        self.transcribe_input_bucket = s3.Bucket(
            self, Image.images_bucket_name,
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        # and for transcribe output
        self.transcribe_output_bucket = s3.Bucket(
            self, Image.bda_output_bucket_name,
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )


        audio_processor_role = iam.Role(self, "AudioProcessorRole",
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

        self.audio_processing_function = lmbd.DockerImageFunction(self, "AudioTranscribeOrchestrator",
                                                           timeout=Duration.seconds(30),
                                                           # Timeout is short, as it only STARTS the job
                                                           code=lmbd.DockerImageCode.from_image_asset(
                                                               directory=os.path.join(functions_root,
                                                                                      "audio_processing")),
                                                           memory_size=256,
                                                           role=audio_processor_role,
                                                           vpc=vpc_stack.vpc,
                                                           security_groups=[db_stack.db_sec_group],
                                                           environment={
                                                               'TRANSCRIBE_BUCKET_IN': self.transcribe_input_bucket.bucket_name,
                                                           }
                                                           )


        self.transcribe_input_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.audio_processing_function)
        )

        audio_processed_results_role = iam.Role(self, "AudioProcessorRole",
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
        self.transcribe_output_bucket.greant_read(audio_processed_results_role)
        db_stack.db_secret.grant_read(audio_processed_results_role)

        self.transcribe_output_processing_function = lmbd.DockerImageFunction(self, Image.func_bda_out_name,
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
                                                                                  'SNS_TOPIC_ARN': text_stack.text_processing_topic.topic_arn
                                                                              })

        self.transcribe_input_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.transcribe_output_processing_function)
        )
