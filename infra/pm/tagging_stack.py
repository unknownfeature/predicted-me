from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_lambda_event_sources as lmes,
    aws_sns_subscriptions as subs)
from constructs import Construct

from .db_stack import PmDbStack
from .util import docker_code_asset, setup_bedrock_lambda_role
from .vpc_stack import PmVpcStack
from shared.variables import Env, Common, Tagging


class PmTaggingStack(Stack):

    def __init__(self, scope: Construct, db_stack: PmDbStack, vpc_stack: PmVpcStack, **kwargs) -> None:
        super().__init__(scope, Tagging.stack_name, **kwargs)

        self.tagging_topic = sns.Topic(self, Tagging.tagging_topic_name,
                                       display_name=Tagging.tagging_topic_name,
                                       topic_name=Tagging.tagging_topic_name
                                       )

        self.metrics_tagging_queue = sqs.Queue(self, Tagging.metrics_tagging_queue_name,
                                               queue_name=Tagging.metrics_tagging_queue_name,
                                               visibility_timeout=Tagging.metrics_tagging_queue_visibility_timeout
                                               )
        
        self.links_tagging_queue = sqs.Queue(self, Tagging.links_tagging_queue_name,
                                               queue_name=Tagging.links_tagging_queue_name,
                                               visibility_timeout=Tagging.links_tagging_queue_visibility_timeout
                                               )
        
        self.tasks_tagging_queue = sqs.Queue(self, Tagging.tasks_tagging_queue_name,
                                               queue_name=Tagging.tasks_tagging_queue_name,
                                               visibility_timeout=Tagging.tasks_tagging_queue_visibility_timeout
                                               )
        
        self.tagging_topic.add_subscription(
            subs.SqsSubscription(self.metrics_tagging_queue)
        )
        self.tagging_topic.add_subscription(
            subs.SqsSubscription(self.links_tagging_queue)
        )
        self.tagging_topic.add_subscription(
            subs.SqsSubscription(self.tasks_tagging_queue)
        )

        self.metrics_tagging_tole = setup_bedrock_lambda_role(self, db_stack, Tagging.metrics_tagging_role)

        self.metrics_tagging_function = lmbd.DockerImageFunction(self, Tagging.metrics_tagging_func_name,
                                                                 timeout=Tagging.metrics_tagging_func_timeout,
                                                                 code=docker_code_asset(
                                                             build_args={
                                                                 Common.func_dir_arg: Tagging.metrics_tagging_func_code_path,
                                                                 Common.install_mysql_arg: 'True',
                                                             }
                                                         ),
                                                                 memory_size=Tagging.metrics_tagging_func_memory_size,
                                                                 vpc=vpc_stack.vpc,
                                                                 role=self.metrics_tagging_tole,
                                                                 security_groups=[db_stack.db_sec_group],
                                                                 environment={
                                                             Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                             Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                             Env.db_name: db_stack.db_instance.instance_identifier,
                                                             Env.generative_model: Tagging.tagging_model_name,

                                                         }
                                                                 )

        self.metrics_tagging_function.add_event_source(
            lmes.SqsEventSource(self.metrics_tagging_queue)
        )

        db_stack.db_instance.connections.allow_default_port_from(self.metrics_tagging_function)

        self.links_tagging_tole = setup_bedrock_lambda_role(self, db_stack, Tagging.links_tagging_role)

        self.links_tagging_function = lmbd.DockerImageFunction(self, Tagging.links_tagging_func_name,
                                                                 timeout=Tagging.links_tagging_func_timeout,
                                                                 code=docker_code_asset(
                                                                     build_args={
                                                                         Common.func_dir_arg: Tagging.links_tagging_func_code_path,
                                                                         Common.install_mysql_arg: 'True',
                                                                     }
                                                                 ),
                                                                 memory_size=Tagging.links_tagging_func_memory_size,
                                                                 vpc=vpc_stack.vpc,
                                                                 role=self.links_tagging_tole,
                                                                 security_groups=[db_stack.db_sec_group],
                                                                 environment={
                                                                     Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                     Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                     Env.db_name: db_stack.db_instance.instance_identifier,
                                                                     Env.generative_model: Tagging.tagging_model_name,

                                                                 }
                                                                 )

        self.links_tagging_function.add_event_source(
            lmes.SqsEventSource(self.links_tagging_queue)
        )
        db_stack.db_instance.connections.allow_default_port_from(self.links_tagging_function)

        self.tasks_tagging_tole = setup_bedrock_lambda_role(self, db_stack, Tagging.tasks_tagging_role)

        self.tasks_tagging_function = lmbd.DockerImageFunction(self, Tagging.tasks_tagging_func_name,
                                                                 timeout=Tagging.tasks_tagging_func_timeout,
                                                                 code=docker_code_asset(
                                                                     build_args={
                                                                         Common.func_dir_arg: Tagging.tasks_tagging_func_code_path,
                                                                         Common.install_mysql_arg: 'True',
                                                                     }
                                                                 ),
                                                                 memory_size=Tagging.tasks_tagging_func_memory_size,
                                                                 vpc=vpc_stack.vpc,
                                                                 role=self.tasks_tagging_tole,
                                                                 security_groups=[db_stack.db_sec_group],
                                                                 environment={
                                                                     Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                     Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                     Env.db_name: db_stack.db_instance.instance_identifier,
                                                                     Env.generative_model: Tagging.tagging_model_name,

                                                                 }
                                                                 )

        self.tasks_tagging_function.add_event_source(
            lmes.SqsEventSource(self.tasks_tagging_queue)
        )
        db_stack.db_instance.connections.allow_default_port_from(self.tasks_tagging_function)


