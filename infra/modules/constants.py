from aws_cdk import Duration

aws_account= 'AWS_ACCOUNT'
aws_region= 'AWS_REGION'
db_user='DB_USER'
db_pass='DB_PASS'
db_name='DB_NAME'
bastion_instance_key_name='BASTION_INSTANCE_KEY_NAME'
regional_domain_name='REGIONAL_DOMAIN_NAME'
regional_hosted_zone_id='REGIONAL_HOSTED_ZONE_ID'
functions_root = '../backend/functions/'
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

class Cognito:
    stack_name = 'PmCognitoStack'
    pool_name = 'pm_user_pool'
    client = 'pm_client'
    ver_email_subj = 'Please, verify your email'
    ver_email_body = 'Thanks for signing up! Your verification code is {####}'

class Image:
    stack_name = 'PmImageProcessingStack'
    images_bucket_name = 'pm_images_input_bucket'
    bda_output_bucket_name = 'pm_bda_image_output_bucket'
    bda_role_name = 'pm_bda_role'
    bda_blueprint_name = "pm_image_processing_blueprint"
    bda_model_name = "anthropic.claude-3-sonnet-20240229-v1:0"
    func_bda_in_name = 'pm_image_processing_bda_in'
    func_bda_in_timeout = Duration.seconds(30)
    func_bda_in_memory_size = 1024
    func_bda_in_code_path = 'image_processing/bda_in'
    func_bda_in_role_name = 'pm_image_processing_func_role'
    func_bda_out_name = 'pm_image_processing_bda_out'
    func_bda_out_timeout = Duration.minutes(1)
    func_bda_out_memory_size = 2048
    func_bda_out_code_path = 'image_processing/bda_out'
    func_bda_out_role_name = ' DbWriterRole'


class Async:
    stack_name = 'PmAsyncStack'
    text_processing_queue_name = 'pm_text_processing'
    image_processing_queue_name = 'pm_image_processing'
    nutrients_extraction_queue_name = 'pm_nutrients'
    csv_processing_queue_name = 'pm_csv_processing'
    errors_handling_queue_name = 'pm_csv_errors'
    media_bucket_name = 'predictedme-bucket-media'
    csv_bucket_name = 'predictedme-bucket-csv'
    filter_media = 'uploads/*'


class Func:
    stack_name = 'PmFuncStack'

class Api:
    stack_name = 'PmApiStack'
    name = 'predictedme-api'
    authorizer = 'predictedme-authorizer'
    api_url = 'api.predicted.me'