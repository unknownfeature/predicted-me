import os

from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda as lmbd,
    aws_iam as iam,
    aws_lambda_event_sources as lmes,
    aws_sns_subscriptions as subs)
from constructs import Construct
from shared.variables import Env, Common, Text, Db
from .db_stack import PmDbStack
from .vpc_stack import PmVpcStack
from .tagging_stack import PmTaggingStack
from .util import docker_code_asset, setup_bedrock_lambda_role

class PmTextStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack, db_stack: PmDbStack, tagging_stack: PmTaggingStack,
                 **kwargs) -> None:
        super().__init__(scope, Text.stack_name, **kwargs)

        self.text_processing_topic = sns.Topic(self, Text.text_topic_name,
                                               display_name=Text.text_topic_name,
                                               topic_name=Text.text_topic_name
                                               )


        self.metrics_extraction_queue = sqs.Queue(self, Text.metrics_extraction_queue_name,
                                                  queue_name=Text.metrics_extraction_queue_name,
                                                  visibility_timeout=Text.metrics_extraction_queue_visibility_timeout
                                                  )
        
        self.links_extraction_queue = sqs.Queue(self, Text.links_extraction_queue_name,
                                                  queue_name=Text.links_extraction_queue_name,
                                                  visibility_timeout=Text.links_extraction_queue_visibility_timeout
                                                  )
        
        self.tasks_extraction_queue = sqs.Queue(self, Text.tasks_extraction_queue_name,
                                                  queue_name=Text.tasks_extraction_queue_name,
                                                  visibility_timeout=Text.tasks_extraction_queue_visibility_timeout
                                                  )

        self.text_processing_topic.add_subscription(
            subs.SqsSubscription(self.metrics_extraction_queue)
        )

        self.text_processing_topic.add_subscription(
            subs.SqsSubscription(self.links_extraction_queue)
        )
        self.text_processing_topic.add_subscription(
            subs.SqsSubscription(self.tasks_extraction_queue)
        )
        
        self.metrics_extraction_role = setup_bedrock_lambda_role(self, db_stack, Text.metrics_extraction_role) 
       

        self.metrics_extraction_function = lmbd.DockerImageFunction(self, Text.metrics_extraction_func_name,
                                                                    timeout=Text.metrics_extraction_func_timeout,
                                                                    code=docker_code_asset(
                                                                        build_args={
                                                                            Common.func_dir_arg: Text.metrics_extraction_func_code_path,
                                                                            Common.install_mysql_arg: 'True',
                                                                        }
                                                                    ),
                                                                    memory_size=Text.metrics_extraction_func_memory_size,
                                                                    vpc=vpc_stack.vpc,
                                                                    role=self.metrics_extraction_role,
                                                                    security_groups=[db_stack.db_sec_group],

                                                                    environment={
                                                                     Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                     Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                     Env.db_name: db_stack.db_instance.instance_identifier,
                                                                     Env.generative_model: Text.text_processing_model,
                                                                     Env.tagging_topic_arn: tagging_stack.tagging_topic.topic_arn,
                                                                     Env.max_tokens: Text.metrics_extraction_max_tokens

                                                                 }
                                                                    )



        self.metrics_extraction_function.add_event_source(
            lmes.SqsEventSource(self.metrics_extraction_queue)
        )
        db_stack.db_instance.connections.allow_default_port_from(self.metrics_extraction_function)

        self.links_extraction_role = setup_bedrock_lambda_role(self, db_stack, Text.links_extraction_role)

        self.links_extraction_function = lmbd.DockerImageFunction(self, Text.links_extraction_func_name,
                                                                    timeout=Text.links_extraction_func_timeout,
                                                                    code=docker_code_asset(
                                                                        build_args={
                                                                            Common.func_dir_arg: Text.links_extraction_func_code_path,
                                                                            Common.install_mysql_arg: 'True',
                                                                        }
                                                                    ),
                                                                    memory_size=Text.links_extraction_func_memory_size,
                                                                    vpc=vpc_stack.vpc,
                                                                    role=self.links_extraction_role,
                                                                    security_groups=[db_stack.db_sec_group],

                                                                    environment={
                                                                        Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                        Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                        Env.db_name: db_stack.db_instance.instance_identifier,
                                                                        Env.generative_model: Text.text_processing_model,
                                                                        Env.tagging_topic_arn: tagging_stack.tagging_topic.topic_arn,
                                                                        Env.max_tokens: Text.links_extraction_max_tokens

                                                                    }
                                                                    )

        self.links_extraction_function.add_event_source(
            lmes.SqsEventSource(self.links_extraction_queue)
        )
        db_stack.db_instance.connections.allow_default_port_from(self.links_extraction_function)

        
        self.tasks_extraction_role = setup_bedrock_lambda_role(self, db_stack, Text.tasks_extraction_role)

        self.tasks_extraction_function = lmbd.DockerImageFunction(self, Text.tasks_extraction_func_name,
                                                                    timeout=Text.tasks_extraction_func_timeout,
                                                                    code=docker_code_asset(
                                                                        build_args={
                                                                            Common.func_dir_arg: Text.tasks_extraction_func_code_path,
                                                                            Common.install_mysql_arg: 'True',
                                                                        }
                                                                    ),
                                                                    memory_size=Text.tasks_extraction_func_memory_size,
                                                                    vpc=vpc_stack.vpc,
                                                                    role=self.tasks_extraction_role,
                                                                    security_groups=[db_stack.db_sec_group],

                                                                    environment={
                                                                        Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                                                                        Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                                                                        Env.db_name: db_stack.db_instance.instance_identifier,
                                                                        Env.db_port: Db.port,
                                                                        Env.generative_model: Text.text_processing_model,
                                                                        Env.tagging_topic_arn: tagging_stack.tagging_topic.topic_arn,
                                                                        Env.max_tokens: Text.tasks_extraction_max_tokens

                                                                    }
                                                                    )

        self.tasks_extraction_function.add_event_source(
            lmes.SqsEventSource(self.tasks_extraction_queue)
        )
        db_stack.db_instance.connections.allow_default_port_from(self.tasks_extraction_function)



