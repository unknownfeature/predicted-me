from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd)
from constructs import Construct

from shared.variables import Env, Common, Text, QueueFunction
from .constants import true, bedrock_invoke_policy_statement
from .db_stack import PmDbStack
from .function_factories import FunctionFactoryParams, create_role_with_db_access_factory, sqs_integration_cb_factory
from .tagging_stack import PmTaggingStack
from .util import create_function, create_queue
from .vpc_stack import PmVpcStack


class PmTextStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, tagging_stack: PmTaggingStack,
                 **kwargs) -> None:
        super().__init__(scope, Text.stack_name, **kwargs)



        self.text_processing_topic = sns.Topic(self, Text.topic_name, display_name=Text.topic_name,
                                       topic_name=Text.topic_name)

        self.metrics_extraction_queue = create_queue(self, Text.metrics_extraction.integration.name,
                                                     visibility_timeout=Text.metrics_extraction.integration.visibility_timeout,
                                                     with_subscription_to=self.text_processing_topic, max_retires=Text.metrics_extraction.integration.max_retries)

        self.links_extraction_queue = create_queue(self, Text.links_extraction.integration.name,
                                                   visibility_timeout=Text.links_extraction.integration.visibility_timeout,
                                                   with_subscription_to=self.text_processing_topic, max_retires=Text.links_extraction.integration.max_retries)

        self.tasks_extraction_queue = create_queue(self, Text.tasks_extraction.integration.name,
                                                   visibility_timeout=Text.tasks_extraction.integration.visibility_timeout,
                                                   with_subscription_to=self.text_processing_topic, max_retires=Text.tasks_extraction.integration.max_retries)

       

        self.metrics_extraction_function = self._create_sqs_triggered_function(db_stack, self.metrics_extraction_queue,
                                                                            vpc_stack, Text.metrics_extraction)
        

        self.links_extraction_function = self._create_sqs_triggered_function(db_stack, self.links_extraction_queue,
                                                                            vpc_stack, Text.links_extraction)
        

        self.tasks_extraction_function = self._create_sqs_triggered_function(db_stack, self.tasks_extraction_queue,
                                                                            vpc_stack, Text.tasks_extraction)
     

    def _create_sqs_triggered_function(self, db_stack: PmDbStack, queue: sqs.Queue, vpc_stack: PmVpcStack,
                                           function_params: QueueFunction) -> lmbd.Function:
            params = FunctionFactoryParams(function_params=function_params,
                                           build_args={Common.func_dir_arg: function_params.code_path,
                                                       Common.install_mysql_arg: true}, environment={
                    Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                    Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    Env.db_name: db_stack.db_instance.instance_identifier,
                    Env.db_port: db_stack.db_instance.db_instance_endpoint_port,
                    Env.max_tokens: Text.max_tokens,
                    Env.generative_model: Text.model,
                }, role_supplier=create_role_with_db_access_factory(db_stack.db_proxy, lambda role: role.add_to_policy(
                    bedrock_invoke_policy_statement)),
                                           and_then=sqs_integration_cb_factory([queue]),
                                           vpc=vpc_stack.vpc)

            return create_function(self, params)




