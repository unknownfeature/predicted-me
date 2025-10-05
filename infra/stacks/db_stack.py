import os

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_rds as rds,
    custom_resources as cr,
    aws_lambda as lmbd,
    aws_events as events,
    aws_events_targets as targets,
    aws_ec2 as ec2)
from constructs import Construct

from backend.tests.integration.functions.data import data_one_units
from shared.variables import Env, Vpc, Db, Common
from .util import docker_code_asset
from .vpc_stack import PmVpcStack


class PmDbStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack,
                 **kwargs) -> None:
        super().__init__(scope, Db.stack_name, **kwargs)

        self.db_sec_group = ec2.SecurityGroup(self, vpc=vpc_stack.vpc, id=Db.sec_group)
        self.db_sec_group.add_ingress_rule(ec2.Peer.ipv4(Vpc.cidr), ec2.Port.tcp(Db.port))

        self.db_secret = rds.DatabaseSecret(self, Db.secret,
                                            username=os.getenv(Env.db_user)
                                            )
        self.db_creds = rds.Credentials.from_secret(self.db_secret)

        self.db_subnet_group = rds.SubnetGroup(self, Db.subnet_group,
                                               description=Db.subnet_group,
                                               vpc=vpc_stack.vpc, removal_policy=cdk.RemovalPolicy.DESTROY,
                                               subnet_group_name=Db.subnet_group,
                                               vpc_subnets=ec2.SubnetSelection(
                                                   subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
                                               )

        self.db_instance = rds.DatabaseInstance(self, Db.instance_name,
                                                engine=rds.DatabaseInstanceEngine.mysql(
                                                    version=rds.MysqlEngineVersion.VER_8_0_35,
                                                ),
                                                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3,
                                                                                  ec2.InstanceSize.XLARGE),
                                                vpc=vpc_stack.vpc,
                                                security_groups=[self.db_sec_group],
                                                database_name=os.getenv(Env.db_name),
                                                credentials=self.db_creds,
                                                subnet_group=self.db_subnet_group,

                                                )

        self.db_initializer_lambda = lmbd.DockerImageFunction(self, Db.initializer_function_name,
                                                              timeout=Db.initializer_function_timeout,
                                                              code=docker_code_asset(
                                                                  build_args={
                                                                      Common.func_dir_arg: Db.initializer_function_code_path,
                                                                      Common.install_mysql_arg: 'True',
                                                                  }
                                                              ),
                                                              memory_size=Db.initializer_function_memory_size,
                                                              vpc=vpc_stack.vpc,
                                                              security_groups=[self.db_sec_group],

                                                              environment={
                                                                  Env.db_secret_arn: self.db_secret.secret_full_arn,
                                                                  Env.db_endpoint: self.db_instance.db_instance_endpoint_address,
                                                                  Env.db_name: self.db_instance.instance_identifier,
                                                                  Env.db_port: Db.port,

                                                              })

        self.db_instance.connections.allow_default_port_from(self.db_initializer_lambda)
        self.db_secret.grant_read(self.db_initializer_lambda)

        provider = cr.Provider(self, Db.initialization_provider, on_event_handler=self.db_initializer_lambda)
        cdk.CustomResource(self, Db.initialization_resource,
                           service_token=provider.service_token,
                           properties={
                               Env.db_secret_arn: self.db_secret.secret_full_arn,
                               Env.db_endpoint: self.db_instance.db_instance_endpoint_address,
                               Env.db_name: self.db_instance.instance_identifier,
                               Env.db_port: Db.port,
                           })

        # todo move this to a separate stack
        self.data_cleanup_lambda = lmbd.DockerImageFunction(self, Db.data_cleanup_function_name,
                                                              timeout=Db.data_cleanup_function_timeout,
                                                              code=docker_code_asset(
                                                                  build_args={
                                                                      Common.func_dir_arg: Db.data_cleanup_function_code_path,
                                                                      Common.install_mysql_arg: 'True',
                                                                  }
                                                              ),
                                                              memory_size=Db.data_cleanup_function_memory_size,
                                                              vpc=vpc_stack.vpc,
                                                              security_groups=[self.db_sec_group],

                                                              environment={
                                                                  Env.db_secret_arn: self.db_secret.secret_full_arn,
                                                                  Env.db_endpoint: self.db_instance.db_instance_endpoint_address,
                                                                  Env.db_name: self.db_instance.instance_identifier,
                                                                  Env.db_port: Db.port,

                                                              })


        self.db_instance.connections.allow_default_port_from( self.data_cleanup_lambda)
        self.db_secret.grant_read( self.data_cleanup_lambda)


        daily_rule = events.Rule(self, Db.data_cleanup_rule_name,
                                 schedule=events.Schedule.cron(
                                     minute="0",
                                     hour="0" ))

        daily_rule.add_target(targets.LambdaFunction(self.data_cleanup_lambda))

        self.occurrencecleanup_lambda = lmbd.DockerImageFunction(self, Db.occurrencecleanup_function_name,
                                                            timeout=Db.occurrencecleanup_function_timeout,
                                                            code=docker_code_asset(
                                                                build_args={
                                                                    Common.func_dir_arg: Db.occurrencecleanup_function_code_path,
                                                                    Common.install_mysql_arg: 'True',
                                                                }
                                                            ),
                                                            memory_size=Db.occurrencecleanup_function_memory_size,
                                                            vpc=vpc_stack.vpc,
                                                            security_groups=[self.db_sec_group],

                                                            environment={
                                                                Env.db_secret_arn: self.db_secret.secret_full_arn,
                                                                Env.db_endpoint: self.db_instance.db_instance_endpoint_address,
                                                                Env.db_name: self.db_instance.instance_identifier,
                                                                Env.db_port: Db.port,

                                                            })

        self.db_instance.connections.allow_default_port_from(self.occurrencecleanup_lambda)
        self.db_secret.grant_read(self.occurrencecleanup_lambda)

        daily_rule = events.Rule(self, Db.occurrence_cleanup_rule_name,
                                 schedule=events.Schedule.cron(
                                     minute="0",
                                     hour="0"))

        daily_rule.add_target(targets.LambdaFunction(self.occurrencecleanup_lambda))

