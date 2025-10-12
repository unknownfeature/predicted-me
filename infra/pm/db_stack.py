import os

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_lambda as lmbd,
    aws_ec2 as ec2)
from constructs import Construct

from shared.variables import Env
from .input import Vpc, Db, Common, ScheduledFunction, CustomResourceTriggeredFunction
from .constants import true
from .function_factories import FunctionFactoryParams, create_role_with_db_access_factory, schedule_cb_factory, \
    custom_resource_trigger_cb_factory, allow_connection_function_factory
from .util import create_function
from .vpc_stack import PmVpcStack


class PmDbStack(Stack):

    def __init__(self, scope: Construct, vpc_stack: PmVpcStack,
                 **kwargs) -> None:
        super().__init__(scope, Db.stack_name, **kwargs)

        self.db_sec_group = ec2.SecurityGroup(self, vpc=vpc_stack.vpc, id=Db.sec_group)
        self.db_sec_group.add_ingress_rule(ec2.Peer.ipv4(Vpc.cidr), ec2.Port.tcp(Db.port))

        self.db_secret = rds.DatabaseSecret(self, Db.secret,
                                            username=os.getenv(Env.db_user))

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
                                                    version=rds.MysqlEngineVersion.VER_8_4_6,
                                                ),
                                                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3,
                                                                                  ec2.InstanceSize.XLARGE),
                                                vpc=vpc_stack.vpc,
                                                security_groups=[self.db_sec_group],
                                                database_name=os.getenv(Env.db_name),
                                                credentials=self.db_creds,
                                                subnet_group=self.db_subnet_group,

                                                )

        self.db_proxy = rds.DatabaseProxy(self, Db.proxy_name,
                                          proxy_target=rds.ProxyTarget.from_instance(self.db_instance),
                                          secrets=[self.db_secret],
                                          vpc=vpc_stack.vpc,
                                          iam_auth=True
                                          )

        self.initializer_function = self._create_initializer_function(vpc_stack, Db.initializer_function)



    def _create_initializer_function(self, vpc_stack: PmVpcStack,
                                     function_params: CustomResourceTriggeredFunction) -> lmbd.Function:
        env = {
            Env.db_secret_arn: self.db_secret.secret_full_arn,
            Env.db_endpoint: self.db_instance.db_instance_endpoint_address,
            Env.db_name: self.db_instance.instance_identifier,
            Env.db_port: self.db_instance.db_instance_endpoint_port,
        }
        return create_function(self, FunctionFactoryParams(
            function_params=function_params,
            build_args={
                Common.func_dir_arg: function_params.code_path,
                Common.install_mysql_arg: true,
            },
            environment=env,
            role_supplier=create_role_with_db_access_factory(self.db_proxy),
            and_then=allow_connection_function_factory(self.db_proxy, custom_resource_trigger_cb_factory(self, {}, function_params )),
            vpc=vpc_stack.vpc,
        ))


