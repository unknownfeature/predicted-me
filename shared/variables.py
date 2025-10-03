import os
from dotenv import load_dotenv
from aws_cdk import Duration

from aws_cdk import aws_apigatewayv2_alpha as api_gtw
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
    bda_input_bucket_name = 'BDA_INPUT_BUCKET_NAME'
    bda_job_execution_role_arn = 'BDA_JOB_EXECUTION_ROLE_ARN'
    bda_blueprint_name = 'BDA_BLUEPRINT_NAME'
    bda_model_name = 'BDA_MODEL_NAME'
    transcribe_bucket_in = 'TRANSCRIBE_BUCKET_IN'
    transcribe_bucket_out = 'TRANSCRIBE_BUCKET_OUT'

    bastion_ami = 'BASTION_AMI'
    bastion_instance_key_name = 'BASTION_INSTANCE_KEY_NAME'

    regional_domain_name = 'REGIONAL_DOMAIN_NAME'
    regional_hosted_zone_id = 'REGIONAL_HOSTED_ZONE_ID'
    max_tokens = 'MAX_TOKENS'


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
    backend_dir_arg = 'BACKEND_DIR'
    install_mysql_arg = 'INSTALL_MYSQL'
    lib_path = os.path.join(backend_dir, lib_dir)
    shared_path = os.path.join(backend_dir, shared_dir)
    docker_path = docker_file_dir

    default_region = 'us-east-1'
    generative_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    cors_headers = {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,GET'
    }


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
    func_transcribe_in_code_path = os.path.join(Common.functions_dir,
                                                'audio_processing/transcribe_in')
    func_transcribe_in_role_name = 'pm_audio_processing_func_role'
    func_transcribe_out_name = 'pm_audio_processing_transcribe_out'
    func_transcribe_out_timeout = Duration.minutes(1)
    func_transcribe_out_memory_size = 2048
    func_transcribe_out_code_path = os.path.join(Common.functions_dir,
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
    func_bda_in_code_path = os.path.join(Common.functions_dir, 'image_processing/bda_in')
    func_bda_in_role_name = 'pm_bda_in_function'
    func_bda_out_name = 'pm_image_processing_bda_out'
    func_bda_out_timeout = Duration.minutes(1)
    func_bda_out_memory_size = 2048
    func_bda_out_code_path = os.path.join(Common.functions_dir, 'image_processing/bda_out')
    func_bda_out_role_name = 'pm_bda_out_function'


class Text:
    stack_name = 'PmTextStack'
    text_topic_name = 'pm_text_processing_topic'
    metrics_extraction_func_name = 'pm_metrics_extraction_func'
    metrics_extraction_func_timeout = Duration.minutes(1)
    metrics_extraction_func_memory_size = 1024
    metrics_extraction_func_code_path = os.path.join(Common.functions_dir, 'text/metrics')
    metrics_extraction_queue_name = 'pm_metrics_extraction_queue'
    metrics_extraction_queue_visibility_timeout = Duration.minutes(2)
    metrics_extraction_role = 'pm_metrics_extraction_role'
    metrics_extraction_max_tokens = 1024
    
    links_extraction_func_name = 'pm_links_extraction_func'
    links_extraction_func_timeout = Duration.minutes(1)
    links_extraction_func_memory_size = 1024
    links_extraction_func_code_path = os.path.join(Common.functions_dir, 'text/links')
    links_extraction_queue_name = 'pm_links_extraction_queue'
    links_extraction_queue_visibility_timeout = Duration.minutes(2)
    links_extraction_role = 'pm_links_extraction_role'
    links_extraction_max_tokens = 1024
    
    tasks_extraction_func_name = 'pm_tasks_extraction_func'
    tasks_extraction_func_timeout = Duration.minutes(1)
    tasks_extraction_func_memory_size = 1024
    tasks_extraction_func_code_path = os.path.join(Common.functions_dir, 'text/tasks')
    tasks_extraction_queue_name = 'pm_tasks_extraction_queue'
    tasks_extraction_queue_visibility_timeout = Duration.minutes(2)
    tasks_extraction_role = 'pm_tasks_extraction_role'
    tasks_extraction_max_tokens = 1024
    
    text_processing_model = Common.generative_model



class Tagging:
    stack_name = 'PmTaggingStack'
    tagging_topic_name = 'pm_tagging_topic'
    metrics_tagging_queue_name = 'pm_metrics_tagging_queue'
    metrics_tagging_queue_visibility_timeout = Duration.minutes(2)
    metrics_tagging_role = 'pm_metrics_tagging_writer_role'
    metrics_tagging_func_name = 'pm_metrics_tagging_func'
    metrics_tagging_func_timeout = Duration.minutes(1)
    metrics_tagging_func_memory_size = 2048
    metrics_tagging_func_code_path = os.path.join(Common.functions_dir, 'tagging/metrics')
    metrics_tagging_func_role_name = 'pm_metrics_tagging_writer_role'
    
    links_tagging_queue_name = 'pm_links_tagging_queue'
    links_tagging_queue_visibility_timeout = Duration.minutes(2)
    links_tagging_role = 'pm_links_tagging_writer_role'
    links_tagging_func_name = 'pm_links_tagging_func'
    links_tagging_func_timeout = Duration.minutes(1)
    links_tagging_func_memory_size = 2048
    links_tagging_func_code_path = os.path.join(Common.functions_dir, 'tagging/links')
    links_tagging_func_role_name = 'pm_links_tagging_writer_role'
    
    tasks_tagging_queue_name = 'pm_tasks_tagging_queue'
    tasks_tagging_queue_visibility_timeout = Duration.minutes(2)
    tasks_tagging_role = 'pm_tasks_tagging_writer_role'
    tasks_tagging_func_name = 'pm_tasks_tagging_func'
    tasks_tagging_func_timeout = Duration.minutes(1)
    tasks_tagging_func_memory_size = 2048
    tasks_tagging_func_code_path = os.path.join(Common.functions_dir, 'tagging/tasks')
    tasks_tagging_func_role_name = 'pm_tasks_tagging_writer_role'

    tagging_model_name = Common.generative_model


class Api:
    stack_name = 'PmApiStack'
    name = 'pm_api'
    authorizer = 'pm_authorizer'
    api_url = 'api.predicted.me'

    presign_function_name = 'pm_presign_function'
    presign_function_timeout = Duration.minutes(1)
    presign_function_memory_size = 1024
    presign_function_code_path = os.path.join(Common.functions_dir, 'presign/index')
    presign_function_role_name = 'pm_presign_function_role'

    presign_function_url_path = '/presign'
    presign_function_methods = [api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS]
    presign_function_integration =  'pm_presign_function_integration'

    note_api_function_name = 'pm_note_api_function'
    note_api_function_timeout = Duration.minutes(1)
    note_api_function_memory_size = 1024
    note_api_function_code_path = os.path.join(Common.functions_dir, 'note_api/index')
    note_api_function_role_name = 'pm_note_api_function_role'

    note_api_function_url_path = '/note'
    note_api_function_methods =  [api_gtw.HttpMethod.POST, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS]
    note_api_function_integration =  'pm_note_api_function_integration'

    data_api_function_name = 'pm_data_api_function'
    data_api_function_timeout = Duration.minutes(1)
    data_api_function_memory_size = 1024
    data_api_function_code_path = os.path.join(Common.functions_dir, 'data_api/index')
    data_api_function_role_name = 'pm_data_api_function_role'

    data_api_function_url_path = '/data'
    data_api_function_methods =  [api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS]
    data_api_function_integration =  'pm_data_api_function_integration'

    link_api_function_name = 'pm_link_api_function'
    link_api_function_timeout = Duration.minutes(1)
    link_api_function_memory_size = 1024
    link_api_function_code_path = os.path.join(Common.functions_dir, 'link_api/index')
    link_api_function_role_name = 'pm_link_api_function_role'

    link_api_function_url_path = '/link'
    link_api_function_methods =  [api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS]
    link_api_function_integration =  'pm_link_api_function_integration'


    schedule_api_function_name = 'pm_schedule_api_function'
    schedule_api_function_timeout = Duration.minutes(1)
    schedule_api_function_memory_size = 1024
    schedule_api_function_code_path = os.path.join(Common.functions_dir, 'schedule_api/index')
    schedule_api_function_role_name = 'pm_schedule_api_function_role'

    schedule_api_function_url_path = '/schedule'
    schedule_api_function_methods =  [api_gtw.HttpMethod.POST, api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.OPTIONS]
    schedule_api_function_integration =  'pm_schedule_api_function_integration'
    
    task_api_function_name = 'pm_task_api_function'
    task_api_function_timeout = Duration.minutes(1)
    task_api_function_memory_size = 1024
    task_api_function_code_path = os.path.join(Common.functions_dir, 'task_api/index')
    task_api_function_role_name = 'pm_task_api_function_role'

    task_api_function_url_path = '/task'
    task_api_function_methods =  [api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS]
    task_api_function_integration =  'pm_task_api_function_integration'
    
    user_api_function_name = 'pm_user_api_function'
    user_api_function_timeout = Duration.minutes(1)
    user_api_function_memory_size = 1024
    user_api_function_code_path = os.path.join(Common.functions_dir, 'user_api/index')
    user_api_function_role_name = 'pm_user_api_function_role'

    user_api_function_url_path = '/user'
    user_api_function_methods =  [api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS]
    user_api_function_integration =  'pm_user_api_function_integration'