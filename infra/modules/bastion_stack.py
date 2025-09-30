import os

from aws_cdk import (
    Stack,
    aws_ec2 as ec2)
from constructs import Construct
from modules.vpc_stack import PmVpcStack
from modules.constants import *


class PmBastionStack(Stack):

    def __init__(self, scope: Construct,  vpc_stack: PmVpcStack, **kwargs) -> None:
        super().__init__(scope, Bastion.stack_name, **kwargs)

        sec_group = ec2.SecurityGroup(self, vpc=vpc_stack.vpc, id=Bastion.sec_group)
        sec_group.add_ingress_rule(ec2.Peer.ipv4(Bastion.sec_group_ingress_allow_cidr), ec2.Port.tcp(Bastion.sec_group_ingress_allow_port))

        ec2.Instance(self, Bastion.instance_name,
                     vpc=vpc_stack.vpc,
                     instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
                     machine_image=ec2.MachineImage.lookup(name=Bastion.ec2_ami),
                     vpc_subnets=ec2.SubnetSelection(
                         subnet_type=ec2.SubnetType.PUBLIC
                     ),
                     security_group=sec_group,
                     key_name=os.getenv(Bastion.bastion_instance_key_name)
                     )
