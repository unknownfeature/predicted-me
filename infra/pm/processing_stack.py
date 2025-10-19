import os

from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd)
from constructs import Construct

from shared.variables import *
from .input import Common, Processing, QueueFunction
from .constants import true, bedrock_invoke_policy_statement
from .db_stack import PmDbStack
from .function_factories import sqs_integration_cb_factory, create_role_with_db_access_factory, FunctionFactoryParams, \
    allow_connection_function_factory
from .util import create_queue, create_function
from .vpc_stack import PmVpcStack


class PmProcessingStack(Stack):

    def __init__(self, scope: Construct, db_stack: PmDbStack, vpc_stack: PmVpcStack, **kwargs) -> None:
        super().__init__(scope, Processing.stack_name, **kwargs)

        self.processing_topic = sns.Topic(self, Processing.topic_name, display_name=Processing.topic_name,
                                          topic_name=Processing.topic_name)

        self.metrics_tagging_queue = create_queue(self, Processing.metric_tagging.integration.name,
                                                  visibility_timeout=Processing.metric_tagging.integration.visibility_timeout,
                                                  with_subscription_to=self.processing_topic, max_retires=Processing.metric_tagging.integration.max_retries)

        self.links_tagging_queue = create_queue(self, Processing.link_tagging.integration.name,
                                                visibility_timeout=Processing.link_tagging.integration.visibility_timeout,
                                                with_subscription_to=self.processing_topic, max_retires=Processing.link_tagging.integration.max_retries)

        self.tasks_tagging_queue = create_queue(self, Processing.task_tagging.integration.name,
                                                visibility_timeout=Processing.task_tagging.integration.visibility_timeout,
                                                with_subscription_to=self.processing_topic, max_retires=Processing.task_tagging.integration.max_retries)
        self.nutrients_extraction_queue = create_queue(self, Processing.nutrients_extraction.integration.name,
                                                visibility_timeout=Processing.nutrients_extraction.integration.visibility_timeout,
                                                with_subscription_to=self.processing_topic, max_retires=Processing.nutrients_extraction.integration.max_retries)

        self.metrics_tagging_function = self._create_sqs_triggered_function(db_stack, self.metrics_tagging_queue,
                                                                            vpc_stack, Processing.metric_tagging)

        self.links_tagging_function = self._create_sqs_triggered_function(db_stack, self.links_tagging_queue, vpc_stack,
                                                                          Processing.link_tagging)

        self.tasks_tagging_function = self._create_sqs_triggered_function(db_stack, self.tasks_tagging_queue, vpc_stack,
                                                                          Processing.task_tagging)
        self.nutrients_extraction_functions = self._create_sqs_triggered_function(db_stack, self.nutrients_extraction_queue, vpc_stack,
                                                                          Processing.nutrients_extraction)

    def _create_sqs_triggered_function(self, db_stack: PmDbStack, queue: sqs.Queue, vpc_stack: PmVpcStack,
                                       function_params: QueueFunction) -> lmbd.Function:
        params = FunctionFactoryParams(function_params=function_params,
                                       build_args={Common.func_dir_arg: function_params.code_path,
                                                   Common.install_mysql_arg: true}, environment={
                db_secret_arn: db_stack.db_secret.secret_full_arn,
                db_endpoint: db_stack.db_proxy.db_instance_endpoint_address,
                db_name: os.getenv(db_name),
                db_port: db_stack.db_proxy.db_instance_endpoint_port,
                generative_model: Processing.model,
                max_tokens: Processing.max_tokens,

            }, role_supplier=create_role_with_db_access_factory(db_stack.db_proxy, db_stack.db_secret, lambda role: role.add_to_policy(
                bedrock_invoke_policy_statement)),
                                       and_then=allow_connection_function_factory(db_stack.db_proxy, sqs_integration_cb_factory([queue])),
                                       vpc=vpc_stack.vpc)

        return create_function(self, params)
