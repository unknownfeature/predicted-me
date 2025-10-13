import os

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_bedrock as bedrock)
from constructs import Construct

from shared.variables import *
from .input import Common, Image
from .constants import true, bedrock_invoke_policy_statement
from .db_stack import PmDbStack
from .function_factories import FunctionFactoryParams, s3_integration_cb_factory, \
    S3EventParams, create_lambda_role, create_role_with_db_access_factory, allow_connection_function_factory
from .text_stack import PmTextStack
from .util import create_bucket, create_function
from .vpc_stack import PmVpcStack


class PmImageStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, text_stack: PmTextStack,
                 **kwargs) -> None:
        super().__init__(scope, Image.stack_name, **kwargs)
        # pre setup blueprint for BDA
        blueprint_schema = {
            'class': 'ImageDescription',
            'description': 'The user wants a concise, detailed, and objective summary of the image content for cataloging purposes. And relevant image text extraction where possible.',
            'inference_schema': {
                'type': 'object',
                'properties': {
                    'image_description': {
                        'type': 'string',
                        'description': 'A single, detailed paragraph describing the image\'s main subject, scene, colors, lighting, and any obvious actions.',
                        'inference_type': 'GENERATIVE_FIELD'
                    },
                    'image_text': {
                        'type': 'string',
                        'description': 'Extract relevant text from the image',
                        'inference_type': 'GENERATIVE_FIELD'
                    }
                },
                'required': ['image_description', 'image_text']
            }
        }

        image_blueprint = bedrock.CfnBlueprint(
            self, Image.bda_blueprint_name,
            blueprint_name=Image.bda_blueprint_name,
            schema=blueprint_schema,
            type='IMAGE'
        )

        self.bda_input_bucket = create_bucket(self, Image.bda_input_bucket_name)
        self.bda_output_bucket = create_bucket(self, Image.bda_output_bucket_name)

        self.bda_in_processing_function = self._create_bda_in_function(image_blueprint)
        self.bda_out_processing_function = self._create_bda_out_function(db_stack, text_stack, vpc_stack)

    def _create_bda_in_function(self, image_blueprint: bedrock.CfnBlueprint) -> lmbd.Function:
        def on_role(role):
            role.add_to_policy(bedrock_invoke_policy_statement)
            role.add_to_policy(iam.PolicyStatement(
                actions=['bedrock-data-automation:StartDataAutomationJob'],
                resources=['*'],
                effect=iam.Effect.ALLOW
            ))

            self.bda_input_bucket.grant_read(role)
            self.bda_output_bucket.grant_write(role)

        role = create_lambda_role(self, Image.bda_in.role_name, on_role)

        params = FunctionFactoryParams(function_params=Image.bda_in,
                                       build_args={Common.func_dir_arg: Image.bda_in.code_path, },
                                       environment={
                                           bda_output_bucket_name: self.bda_output_bucket.bucket_name,
                                           bda_job_execution_role_arn: role.role_arn,
                                           bda_blueprint_name: image_blueprint.blueprint_name,
                                           bda_model_name: Image.bda_model_name,
                                           gemini_api_key: os.getenv(gemini_api_key)

                                       }, role_supplier= lambda _, __: role,
                                       and_then=s3_integration_cb_factory(
                                           [S3EventParams(self.bda_input_bucket, s3.EventType.OBJECT_CREATED)]))

        return create_function(self, params)

    def _create_bda_out_function(self, db_stack: PmDbStack, text_stack: PmTextStack, vpc_stack: PmVpcStack) -> lmbd.Function:
        def on_role(role):
            self.bda_output_bucket.grant_read(role)
            text_stack.text_processing_topic.grant_publish(role)

        params = FunctionFactoryParams(function_params=Image.bda_out, build_args={
            Common.func_dir_arg: Image.bda_out.code_path, Common.install_mysql_arg: true
        }, environment={
            transcribe_bucket_out: self.bda_output_bucket.bucket_name,
            db_secret_arn: db_stack.db_secret.secret_full_arn,
            db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
            db_name: os.getenv(db_name),
            db_port: db_stack.db_instance.db_instance_endpoint_port,
            text_processing_topic_arn: text_stack.text_processing_topic.topic_arn,
        }, role_supplier=create_role_with_db_access_factory(db_stack.db_proxy, db_stack.db_secret, on_role),
            and_then=allow_connection_function_factory( db_stack.db_proxy, s3_integration_cb_factory([S3EventParams(self.bda_output_bucket, s3.EventType.OBJECT_CREATED)])),
            vpc=vpc_stack.vpc)

        return create_function(self, params)
