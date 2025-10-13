import os

from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_opensearchservice as opensearch,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as lmbd, RemovalPolicy)
from constructs import Construct

from shared.variables import *
from .bastion_stack import PmBastionStack
from .input import Common, Text, QueueFunction, CustomResourceTriggeredFunction
from .constants import true, bedrock_invoke_policy_statement
from .db_stack import PmDbStack
from .function_factories import FunctionFactoryParams, create_role_with_db_access_factory, sqs_integration_cb_factory, \
    create_function_role_factory, custom_resource_trigger_cb_factory, allow_connection_function_factory
from .tagging_stack import PmTaggingStack
from .util import create_function, create_queue
from .vpc_stack import PmVpcStack


class PmTextStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, bastion_stack: PmBastionStack,
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

        self.embedding_queue = create_queue(self, Text.embedding.integration.name,
                                                   visibility_timeout=Text.embedding.integration.visibility_timeout,
                                                   with_subscription_to=self.text_processing_topic, max_retires=Text.embedding.integration.max_retries)

        self.metrics_extraction_function = self._create_sqs_triggered_function(db_stack, self.metrics_extraction_queue,
                                                                            vpc_stack, Text.metrics_extraction)
        

        self.links_extraction_function = self._create_sqs_triggered_function(db_stack, self.links_extraction_queue,
                                                                            vpc_stack, Text.links_extraction)
        

        self.tasks_extraction_function = self._create_sqs_triggered_function(db_stack, self.tasks_extraction_queue,
                                                                            vpc_stack, Text.tasks_extraction)

        self.embedding_domain = opensearch.Domain(self, Text.domain,
                                   version=opensearch.EngineVersion.OPENSEARCH_2_17,
                                   vpc=vpc_stack.vpc,
                                   removal_policy=RemovalPolicy.DESTROY,
                                   vpc_subnets=[ec2.SubnetSelection(
                                       subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                                       one_per_az=False,
                                       availability_zones=vpc_stack.vpc.availability_zones[:1]
                                   )],
                                   capacity=opensearch.CapacityConfig(
                                       data_nodes=Text.domain_data_nodes,
                                       data_node_instance_type=Text.domain_data_node_instance_type
                                   ),
                                   ebs=opensearch.EbsOptions(volume_size=Text.domain_ebs_volume_size,),
                                   node_to_node_encryption=True,
                                   encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
                                   enforce_https=True)

        self.embedding_function = self._create_embedding_function(self.embedding_queue, vpc_stack, Text.embedding)
        self.embedding_index_creation_function = self._create_initializer_function(vpc_stack, Text.embedding_index_creator_function)
        self.embedding_domain.connections.allow_from(
            bastion_stack.instance,
            port_range=ec2.Port.tcp(int(Common.opensearch_port))
        )

    def _create_embedding_function(self, queue: sqs.Queue, vpc_stack: PmVpcStack,
                                           function_params: QueueFunction) -> lmbd.Function:
            def on_role(role: iam.Role):
                role.add_to_policy(
                    bedrock_invoke_policy_statement)
                self.embedding_domain.grant_write(role)

            def and_then(func: lmbd.Function):
                self.embedding_domain.connections.allow_from(
                    func,
                    port_range=ec2.Port.tcp(int(Common.opensearch_port)))
                sqs_integration_cb_factory([queue])(func)

            params = FunctionFactoryParams(function_params=function_params,
                                           build_args={Common.func_dir_arg: function_params.code_path},
                                           environment={
                    opensearch_endpoint: self.embedding_domain.domain_endpoint,
                    opensearch_port: Common.opensearch_port,
                    opensearch_index: Text.opensearch_index,
                    embedding_model: Text.embedding_model,

                }, role_supplier=create_function_role_factory(on_role),
                                           and_then=and_then,
                                           vpc=vpc_stack.vpc)

            return create_function(self, params)

    def _create_sqs_triggered_function(self, db_stack: PmDbStack, queue: sqs.Queue, vpc_stack: PmVpcStack,
                                           function_params: QueueFunction) -> lmbd.Function:
            params = FunctionFactoryParams(function_params=function_params,
                                           build_args={Common.func_dir_arg: function_params.code_path,
                                                       Common.install_mysql_arg: true}, environment={
                    db_secret_arn: db_stack.db_secret.secret_full_arn,
                    db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                    db_name: os.getenv(db_name),
                    db_port: db_stack.db_instance.db_instance_endpoint_port,
                    max_tokens: Text.max_tokens,
                    generative_model: Text.generative_model,

                }, role_supplier=create_role_with_db_access_factory(db_stack.db_proxy, db_stack.db_secret, lambda role: role.add_to_policy(
                    bedrock_invoke_policy_statement)),
                                           and_then=allow_connection_function_factory(db_stack.db_proxy, sqs_integration_cb_factory([queue])),
                                           vpc=vpc_stack.vpc)

            return create_function(self, params)

    def _create_initializer_function(self, vpc_stack: PmVpcStack,
                                     function_params: CustomResourceTriggeredFunction) -> lmbd.Function:
        def and_then(function: lmbd.Function):
            self.embedding_domain.connections.allow_from(
            function,
            port_range=ec2.Port.tcp(int(Common.opensearch_port)))
            custom_resource_trigger_cb_factory(self, {}, function_params)(function)

        env = {
            opensearch_endpoint: self.embedding_domain.domain_endpoint,
            opensearch_port: Common.opensearch_port,
            opensearch_index: Text.opensearch_index,
            opensearch_index_refresh_interval: Text.opensearch_index_refresh_interval,
            embedding_vector_dimension: str(Text.embedding_vector_dimension)
        }
        return create_function(self, FunctionFactoryParams(
            function_params=function_params,
            build_args={
                Common.func_dir_arg: function_params.code_path,
            },
            environment=env,
            role_supplier=create_function_role_factory(lambda role:  self.embedding_domain.grant_write(role)),
            and_then=and_then,
            vpc=vpc_stack.vpc,
        ))




