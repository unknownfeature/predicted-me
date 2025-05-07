from aws_cdk import (
    Stack,
    aws_ec2 as ec2)
from constructs import Construct

from constants import *


class PmVpcStack(Stack):

    def __init__(self, scope: Construct, **kwargs) -> None:
        super().__init__(scope, Vpc.stack_name, **kwargs)
        self.vpc = ec2.Vpc(
            self, Vpc.net_prefix, cidr=Vpc.cidr, nat_gateways=0, subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=Vpc.net_prefix + '_public',
                    subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(
                    name=Vpc.net_prefix + '_private',
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
            ], enable_dns_support=True,
            enable_dns_hostnames=True,
        )
