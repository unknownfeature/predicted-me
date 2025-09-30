import os
from dotenv import load_dotenv
from aws_cdk import Duration


load_dotenv()

# env var names
class Env:
    db_secret_arn = 'DB_SECRET_ARN'
    db_endpoint = 'DB_ENDPOINT'
    db_name = 'DB_NAME'
    db_user = 'DB_USER'
    db_pass = 'DB_PASS'
    aws_account = 'AWS_ACCOUNT'
    aws_region = 'AWS_REGION'

    root_dir = 'ROOT_DIR'

    generative_model = 'GENERATIVE_MODEL'
    text_processing_topic_arn = 'TEXT_PROCESSING_TOPIC_ARN'
    tagging_topic_arn = 'TAGGING_TOPIC_ARN'
    bda_output_bucket_name = 'BDA_OUTPUT_BUCKET_NAME'
    bda_job_execution_role_arn = 'BDA_JOB_EXECUTION_ROLE_ARN'
    bda_blueprint_name = 'BDA_BLUEPRINT_NAME'
    bda_model_name = 'BDA_MODEL_NAME'
    transcribe_bucket_in = 'TRANSCRIBE_BUCKET_IN'
    transcribe_bucket_out = 'TRANSCRIBE_BUCKET_OUT'

    bastion_ami = 'BASTION_AMI'
    bastion_instance_key_name = 'BASTION_INSTANCE_KEY_NAME'

    regional_domain_name = 'REGIONAL_DOMAIN_NAME'
    regional_hosted_zone_id = 'REGIONAL_HOSTED_ZONE_ID'


class Common:
    backend_dir = 'backend'
    functions_dir = 'functions'
    lib_dir = 'lib'
    shared_dir = 'shared'
    docker_file_dir = 'docker'
    docker_file = 'Dockerfile'
    lib_dir_arg = 'LIB_PATH'
    shared_path_arg = 'SHARED_PATH'
    func_dir_arg = 'FUNC_DIR'
    install_mysql_arg = 'INSTALL_MYSQL'
    lib_path = os.path.join(backend_dir, lib_dir)
    shared_path = os.path.join(backend_dir, shared_dir)
    func_dir = os.path.join(backend_dir, functions_dir)
    docker_path = os.path.join(backend_dir, docker_file_dir)

    default_region = 'us-east-1'
    generative_model = "anthropic.claude-3-sonnet-20240229-v1:0"


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
    ec2_ami = os.getenv(Env.bastion_ami)
    instance_name = 'pm_bastion_host'
    instance_key_name = os.getenv(Env.bastion_instance_key_name)


class Cognito:
    stack_name = 'PmCognitoStack'
    pool_name = 'pm_user_pool'
    client = 'pm_client'
    ver_email_subj = 'Please, verify your email'
    ver_email_body = 'Thanks for signing up! Your verification code is {####}'


class Audio:
    stack_name = 'PmImageProcessingStack'
    transcribe_input_bucket_name = 'pm_transcribe_audio_input_bucket'
    transcribe_output_bucket_name = 'pm_transcribe_audio_output_bucket'
    func_transcribe_in_name = 'pm_audio_processing_transcribe_in'
    func_transcribe_in_timeout = Duration.seconds(30)
    func_transcribe_in_memory_size = 1024
    func_transcribe_in_code_path = os.path.join(Common.func_dir,
                                                'audio_processing/transcribe_in')
    func_transcribe_in_role_name = 'pm_audio_processing_func_role'
    func_transcribe_out_name = 'pm_audio_processing_transcribe_out'
    func_transcribe_out_timeout = Duration.minutes(1)
    func_transcribe_out_memory_size = 2048
    func_transcribe_out_code_path = os.path.join(Common.func_dir,
                                                 'audio_processing/transcribe_out')
    func_transcribe_out_role_name = 'pm_transcribe_out_function_role'


class Image:
    stack_name = 'PmImageProcessingStack'
    bda_input_bucket_name = 'pm_images_input_bucket'
    bda_output_bucket_name = 'pm_bda_image_output_bucket'
    bda_role_name = 'pm_bda_role'
    bda_blueprint_name = "pm_image_processing_blueprint"
    bda_model_name = Common.generative_model
    func_bda_in_name = 'pm_image_processing_bda_in'
    func_bda_in_timeout = Duration.seconds(30)
    func_bda_in_memory_size = 1024
    func_bda_in_code_path = os.path.join(Common.func_dir, 'image_processing/bda_in')
    func_bda_in_role_name = 'pm_bda_in_function'
    func_bda_out_name = 'pm_image_processing_bda_out'
    func_bda_out_timeout = Duration.minutes(1)
    func_bda_out_memory_size = 2048
    func_bda_out_code_path = os.path.join(Common.func_dir, 'image_processing/bda_out')
    func_bda_out_role_name = 'pm_bda_out_function'


class Text:
    stack_name = 'PmTextStack'
    text_topic_name = 'pm_text_processing_topic'
    text_processing_func_name = 'pm_text_processing'
    text_processing_func_timeout = Duration.minutes(1)
    text_processing_func_memory_size = 1024
    text_processing_func_code_path = os.path.join(Common.func_dir, 'text_processing')
    text_processing_func_role_name = 'pm_text_processing_func_role'
    text_queue_name = 'pm_metrics_extraction_queue'
    text_queue_visibility_timeout = Duration.minutes(2)
    text_processor_role = 'pm_text_processor_writer_role'
    text_processing_model = Common.generative_model


class Tagging:
    stack_name = 'PmTaggingStack'
    tagging_topic_name = 'pm_tagging_topic'
    tagging_queue_name = 'pm_tagging_queue'
    tagging_queue_visibility_timeout = Duration.minutes(2)
    tagging_role = 'pm_tagging_writer_role'
    tagging_func_name = 'pm_tagging_func'
    tagging_func_timeout = Duration.minutes(1)
    tagging_func_memory_size = 2048
    tagging_func_code_path = os.path.join(Common.func_dir, 'metrics_tagging')
    tagging_func_role_name = 'pm_tagging_writer_role'
    tagging_model_name = Common.generative_model


class Api:
    stack_name = 'PmApiStack'
    name = 'pm_api'
    authorizer = 'pm_authorizer'
    api_url = 'api.predicted.me'
