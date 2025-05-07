aws_account= 'AWS_ACCOUNT'
aws_region= 'AWS_REGION'
db_user='DB_USER'
db_pass='DB_PASS'
db_name='DB_NAME'
bastion_instance_key_name='BASTION_INSTANCE_KEY_NAME'

class Vpc:
    stack_name = 'PmVpcStack'
    cidr = '10.0.0.0/24'
    net_prefix = 'pm_vpc'


class Db:
    stack_name = 'PmDbStack'
    instance_name = 'pm_db'
    net_prefix = 'pm_vpc'
    sec_group = 'pm_db_sec_group'
    subnet_group = 'pm_db_subnet_group'
    port = 3306
    secret = 'pm_db_secret'


class Bastion:
    stack_name = 'PmBastionStack'
    sec_group = 'pm_bastion_sec_group'
    sec_group_ingress_allow_cidr = '0.0.0.0/0'
    sec_group_ingress_allow_port = 22
    ec2_ami = 'ami-058a8a5ab36292159'
    instance_name = 'pm_bastion_host'

