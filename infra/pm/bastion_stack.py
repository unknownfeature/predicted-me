import os

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2)
from constructs import Construct

from shared.variables import *
from .input import Bastion
from .db_stack import PmDbStack
from .vpc_stack import PmVpcStack


class PmBastionStack(Stack):

    def __init__(self, scope: Construct,  db_stack: PmDbStack,  vpc_stack: PmVpcStack,  **kwargs) -> None:
        super().__init__(scope, Bastion.stack_name, **kwargs)

        bastion_role = iam.Role(self, Bastion.role,
                                assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))
        db_stack.db_proxy.grant_connect(bastion_role)

        sec_group = ec2.SecurityGroup(self, vpc=vpc_stack.vpc, id=Bastion.sec_group)
        sec_group.add_ingress_rule(ec2.Peer.ipv4(Bastion.sec_group_ingress_allow_cidr), ec2.Port.tcp(Bastion.sec_group_ingress_allow_port))

        self.instance = ec2.Instance(self, Bastion.instance_name,
                     vpc=vpc_stack.vpc,
                     instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
                     machine_image=ec2.MachineImage.lookup(name=Bastion.ec2_ami),
                     vpc_subnets=ec2.SubnetSelection(
                         subnet_type=ec2.SubnetType.PUBLIC
                     ),
                     security_group=sec_group,
                     key_name=os.getenv(Bastion.instance_key_name),
                                     role=bastion_role)
        self.instance.connections.allow_to(db_stack.db_proxy, port_range=ec2.Port.tcp(int(os.getenv(db_port))))



