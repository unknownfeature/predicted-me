from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lmbd,
    aws_iam as iam
)
from constructs import Construct

from shared.variables import *
from .input import Common, Audio
from .constants import true
from .db_stack import PmDbStack
from .function_factories import FunctionFactoryParams, s3_integration_cb_factory, \
    S3EventParams, create_role_with_db_access_factory, create_function_role_factory, allow_connection_function_factory
from .text_stack import PmTextStack
from .util import create_bucket, create_function
from .vpc_stack import PmVpcStack


class PmAudioStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, text_stack: PmTextStack,
                 **kwargs) -> None:
        super().__init__(scope, Audio.stack_name, **kwargs)

        # bucket for transcribe input
        self.transcribe_input_bucket = create_bucket(self, Audio.transcribe_input_bucket_name, )

        # and for transcribe output
        self.transcribe_output_bucket = create_bucket(self, Audio.transcribe_output_bucket_name, )

        self.transcribe_in_function = self._transcribe_in()
        self.transcribe_out_function = self._transcribe_out(db_stack, text_stack, vpc_stack)

    def _transcribe_in(self) -> lmbd.Function:
        def on_role(role):
            role.add_to_policy(iam.PolicyStatement(
                actions=['transcribe:StartTranscriptionJob', 'transcribe:GetTranscriptionJob'],
                resources=['*']
            ))
            role.add_to_policy(iam.PolicyStatement(
                actions=['iam:PassRole'],
                resources=[role.role_arn],
                conditions={
                    'StringEquals': {'iam:PassedToService': 'transcribe.amazonaws.com'}
                }
            ))
            self.transcribe_input_bucket.grant_read(role)
            self.transcribe_output_bucket.grant_write(role)

        params = FunctionFactoryParams(function_params=Audio.transcribe_in,
                                       build_args={Common.func_dir_arg: Audio.transcribe_in.code_path, },
                                       environment={
                                           transcribe_bucket_in: self.transcribe_input_bucket.bucket_name,
                                           transcribe_bucket_out: self.transcribe_output_bucket.bucket_name,

                                       }, role_supplier=create_function_role_factory(on_role),
                                       and_then=s3_integration_cb_factory([S3EventParams(self.transcribe_input_bucket,
                                                                                         s3.EventType.OBJECT_CREATED)]))

        return create_function(self, params)

    def _transcribe_out(self, db_stack: PmDbStack, text_stack: PmTextStack, vpc_stack: PmVpcStack) -> lmbd.Function:
        def on_role(role):
            self.transcribe_output_bucket.grant_read(role)
            text_stack.text_processing_topic.grant_publish(role)

        params = FunctionFactoryParams(function_params=Audio.transcribe_out, build_args={
            Common.func_dir_arg: Audio.transcribe_out.code_path, Common.install_mysql_arg: true
        }, environment={
            transcribe_bucket_out: self.transcribe_output_bucket.bucket_name,
            db_secret_arn: db_stack.db_secret.secret_full_arn,
            db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
            db_name: db_stack.db_instance.instance_identifier,
            db_port: db_stack.db_instance.db_instance_endpoint_port,
            text_processing_topic_arn: text_stack.text_processing_topic.topic_arn,
        }, role_supplier=create_role_with_db_access_factory(db_stack.db_proxy, db_stack.db_secret, on_role),
                                       and_then=allow_connection_function_factory(db_stack.db_proxy,
                                                                                  s3_integration_cb_factory([
                                                                                                                S3EventParams(
                                                                                                                    self.transcribe_output_bucket,
                                                                                                                    s3.EventType.OBJECT_CREATED)])),
                                       vpc=vpc_stack.vpc)

        return create_function(self, params)
