import os

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2)
from constructs import Construct

from shared.variables import Env, Vpc, Db
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
                                               description= Db.subnet_group,
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
