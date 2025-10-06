from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd)
from constructs import Construct

from shared.variables import Env, Common, Tagging, QueueFunction
from .constants import true, bedrock_invoke_policy_statement
from .db_stack import PmDbStack
from .function_factories import sqs_integration_cb_factory, create_role_with_db_access_factory, FunctionFactoryParams
from .util import create_queue, create_function
from .vpc_stack import PmVpcStack


class PmTaggingStack(Stack):

    def __init__(self, scope: Construct, db_stack: PmDbStack, vpc_stack: PmVpcStack, **kwargs) -> None:
        super().__init__(scope, Tagging.stack_name, **kwargs)

        self.tagging_topic = sns.Topic(self, Tagging.topic_name, display_name=Tagging.topic_name,
                                       topic_name=Tagging.topic_name)

        self.metrics_tagging_queue = create_queue(self, Tagging.metrics.integration.name,
                                                  visibility_timeout=Tagging.metrics.integration.visibility_timeout,
                                                  with_subscription_to=self.tagging_topic)

        self.links_tagging_queue = create_queue(self, Tagging.links.integration.name,
                                                visibility_timeout=Tagging.links.integration.visibility_timeout,
                                                with_subscription_to=self.tagging_topic)

        self.tasks_tagging_queue = create_queue(self, Tagging.tasks.integration.name,
                                                visibility_timeout=Tagging.tasks.integration.visibility_timeout,
                                                with_subscription_to=self.tagging_topic)

        self.metrics_tagging_function = self._create_sqs_triggered_function(db_stack, self.metrics_tagging_queue,
                                                                            vpc_stack, Tagging.metrics)

        self.links_tagging_function = self._create_sqs_triggered_function(db_stack, self.links_tagging_queue, vpc_stack,
                                                                          Tagging.links)

        self.tasks_tagging_function = self._create_sqs_triggered_function(db_stack, self.tasks_tagging_queue, vpc_stack,
                                                                          Tagging.tasks)

    def _create_sqs_triggered_function(self, db_stack: PmDbStack, queue: sqs.Queue, vpc_stack: PmVpcStack,
                                       function_params: QueueFunction) -> lmbd.Function:
        params = FunctionFactoryParams(function_params=function_params,
                                       build_args={Common.func_dir_arg: function_params.code_path,
                                                   Common.install_mysql_arg: true}, environment={
                Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                Env.db_name: db_stack.db_instance.instance_identifier,
                Env.db_port: db_stack.db_instance.db_instance_endpoint_port,
                Env.generative_model: Tagging.model,
                Env.max_tokens: Tagging.max_tokens,

            }, role_supplier=create_role_with_db_access_factory(db_stack.db_proxy, lambda role: role.add_to_policy(
                bedrock_invoke_policy_statement)),
                                       and_then=sqs_integration_cb_factory([queue]),
                                       vpc=vpc_stack.vpc)

        return create_function(self, params)
