import os
from typing import List, Iterable
from dotenv import load_dotenv
from aws_cdk import Duration, aws_events as events, aws_apigatewayv2 as api_gtw
load_dotenv()

class Function:
    name: str
    timeout: Duration
    memory_size: int
    code_path: str
    role_name: str

    def __init__(self, name: str, timeout: Duration, memory_size: int, code_path: str, role_name: str):
        self.name = name
        self.timeout = timeout
        self.memory_size = memory_size
        self.code_path = code_path
        self.role_name = role_name


class HttpIntegration:
    url_path: str
    methods: List[api_gtw.HttpMethod]
    name: str

    def __init__(self, url_path: str, methods: List[api_gtw.HttpMethod], name: str):
        self.url_path = url_path
        self.methods = methods
        self.name = name


class QueueIntegration:
    name: str
    visibility_timeout: Duration

    def __init__(self, queue_name: str, visibility_timeout: Duration):
        self.name = queue_name
        self.visibility_timeout = visibility_timeout


class Schedule:
    rule_name: str
    schedule: events.Schedule

    def __init__(self, rule_name: str, schedule: events.Schedule):
        self.rule_name = rule_name
        self.schedule = schedule


class CustomResourceTrigger:
    resource_name: str
    provider_name: str

    def __init__(self, resource_name: str, provider_name: str):
        self.resource_name = resource_name
        self.provider_name = provider_name


class ApiFunction(Function):
    integrations: Iterable[HttpIntegration]

    def __init__(self, name: str, timeout: Duration, memory_size: int, code_path: str, role_name: str,
                 integrations: Iterable[HttpIntegration]):
        super().__init__(name, timeout, memory_size, code_path, role_name)
        self.integrations = integrations


class QueueFunction(Function):
    integration: QueueIntegration

    def __init__(self, name: str, timeout: Duration, memory_size: int, code_path: str, role_name: str,
                 integration: QueueIntegration):
        super().__init__(name, timeout, memory_size, code_path, role_name)
        self.integration = integration


class ScheduledFunction(Function):
    schedule_params: Schedule

    def __init__(self, name: str, timeout: Duration, memory_size: int, code_path: str, role_name: str,
                 schedule_params: Schedule):
        super().__init__(name, timeout, memory_size, code_path, role_name)
        self.schedule_params = schedule_params


class CustomResourceTriggeredFunction(Function):
    trigger: CustomResourceTrigger

    def __init__(self, name: str, timeout: Duration, memory_size: int, code_path: str, role_name: str,
                 trigger: CustomResourceTrigger):
        super().__init__(name, timeout, memory_size, code_path, role_name)
        self.trigger = trigger


class Env:
    db_secret_arn = 'DB_SECRET_ARN'
    db_endpoint = 'DB_ENDPOINT'
    db_name = 'DB_NAME'
    db_user = 'DB_USER'
    db_pass = 'DB_PASS'
    db_port = 'DB_PORT'
    db_test = 'DB_TEST'
    db_region = 'DB_REGION'
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


# --- Common Project Variables ---

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
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PATCH,DELETE'
    }


class Vpc:
    stack_name = 'PmVpcStack'
    cidr = '10.0.0.0/24'
    net_prefix = 'pm_vpc'


class Db:
    stack_name = 'PmDbStack'
    instance_name = 'pm_db'
    sec_group = 'pm_db_sec_group'
    subnet_group = 'pm_db_subnet_group'
    port = 3306
    secret = 'pm_db_secret'

    initializer_function = CustomResourceTriggeredFunction(
        name='pm_db_initializer_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'schema/index'),
        role_name='pm_db_initializer_func_role',
        trigger=CustomResourceTrigger(resource_name='pm_db_initialization_resource',
                                      provider_name='pm_db_initialization_provider')
    )


    data_cleanup_function = ScheduledFunction(
        name='pm_db_data_cleanup_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'recurrent/data/purge/index'),
        role_name='pm_db_data_cleanup_func_role', 
        schedule_params=Schedule(rule_name='pm_db_data_cleanup_rule', schedule=events.Schedule.cron(minute='0', hour='0')),
    )
    
    occurrence_cleanup_function = ScheduledFunction(
        name='pm_db_occurrence_cleanup_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'recurrent/occurrence/purge/index'),
        role_name='pm_db_occurrence_cleanup_func_role', 
        schedule_params=Schedule(rule_name='pm_db_occurrence_cleanup_rule', schedule=events.Schedule.cron(minute='0', hour='0')),
    )


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
    stack_name = 'PmAudioProcessingStack'
    transcribe_input_bucket_name = 'pm_transcribe_audio_input_bucket'
    transcribe_output_bucket_name = 'pm_transcribe_audio_output_bucket'

    transcribe_in = Function(
        name='pm_audio_processing_transcribe_in',
        timeout=Duration.seconds(30),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'audio_processing/transcribe_in'),
        role_name='pm_audio_processing_func_role'
    )
    transcribe_out = Function(
        name='pm_audio_processing_transcribe_out',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path=os.path.join(Common.functions_dir, 'audio_processing/transcribe_out'),
        role_name='pm_transcribe_out_function_role'
    )


class Image:
    stack_name = 'PmImageProcessingStack'
    bda_input_bucket_name = 'pm_images_input_bucket'
    bda_output_bucket_name = 'pm_bda_image_output_bucket'
    bda_role_name = 'pm_bda_role'
    bda_blueprint_name = "pm_image_processing_blueprint"
    bda_model_name = Common.generative_model

    bda_in = Function(
        name='pm_image_processing_bda_in',
        timeout=Duration.seconds(30),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'image_processing/bda_in'),
        role_name='pm_bda_in_function_role'
    )
    bda_out = Function(
        name='pm_image_processing_bda_out',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path=os.path.join(Common.functions_dir, 'image_processing/bda_out'),
        role_name='pm_bda_out_function_role'
    )


class Text:
    stack_name = 'PmTextStack'
    topic_name = 'pm_text_processing_topic'
    model = Common.generative_model
    max_tokens = '1024'

    metrics_extraction = QueueFunction(
        name='pm_metrics_extraction_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'text/metrics'),
        role_name='pm_metrics_extraction_role',
        integration=QueueIntegration(queue_name='pm_metrics_extraction_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    links_extraction = QueueFunction(
        name='pm_links_extraction_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'text/links'),
        role_name='pm_links_extraction_role',
        integration=QueueIntegration(queue_name='pm_links_extraction_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    tasks_extraction = QueueFunction(
        name='pm_tasks_extraction_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'text/tasks'),
        role_name='pm_tasks_extraction_role',
        integration=QueueIntegration(queue_name='pm_tasks_extraction_queue',
                                     visibility_timeout=Duration.minutes(2))
    )


class Tagging:
    stack_name = 'PmTaggingStack'
    topic_name = 'pm_tagging_topic'
    model = Common.generative_model
    max_tokens = '1024'

    metrics = QueueFunction(
        name='pm_metrics_tagging_func',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path=os.path.join(Common.functions_dir, 'tagging/metrics'),
        role_name='pm_metrics_tagging_role',
        integration=QueueIntegration(queue_name='pm_metrics_tagging_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    links = QueueFunction(
        name='pm_links_tagging_func',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path=os.path.join(Common.functions_dir, 'tagging/links'),
        role_name='pm_links_tagging_role',
        integration=QueueIntegration(queue_name='pm_links_tagging_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    tasks = QueueFunction(
        name='pm_tasks_tagging_func',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path=os.path.join(Common.functions_dir, 'tagging/tasks'),
        role_name='pm_tasks_tagging_role',
        integration=QueueIntegration(queue_name='pm_tasks_tagging_queue',
                                     visibility_timeout=Duration.minutes(2))
    )


class Api:
    stack_name = 'PmApiStack'
    name = 'pm_api'
    authorizer = 'pm_authorizer'
    api_url = 'api.predicted.me'

    presign = ApiFunction(
        name='pm_presign_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'presign/index'),
        role_name='pm_presign_function_role', integrations=[HttpIntegration(
            url_path='/presign',
            methods=[api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_presign_function_integration')]
    )

    note = ApiFunction(
        name='pm_note_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'note/index'),
        role_name='pm_note_api_function_role',
        integrations=[HttpIntegration(
            url_path='/note/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_note_api_function_integration'
        )]
    )

    data = ApiFunction(
        name='pm_data_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'data/index'),
        role_name='pm_data_api_function_role',
        integrations=[HttpIntegration(
            url_path='/data/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_data_api_function_integration'
        )]
    )

    link = ApiFunction(
        name='pm_link_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'link/index'),
        role_name='pm_link_api_function_role',
        integrations=[HttpIntegration(
            url_path='/link/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_link_api_function_integration'
        )]
    )

    data_schedule = ApiFunction(
        name='pm_data_schedule_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'schedule/data/index'),
        role_name='pm_data_schedule_api_function_role',
        integrations=[HttpIntegration(
            url_path='/schedule/metric/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.OPTIONS],
            name='pm_data_schedule_api_function_integration'
        )]
    )

    occurrence_schedule = ApiFunction(
        name='pm_occurrence_schedule_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'schedule/occurrence/index'),
        role_name='pm_occurrence_schedule_api_function_role',
        integrations=[HttpIntegration(
            url_path='/schedule/task/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.OPTIONS],
            name='pm_occurrence_schedule_api_function_integration'
        )]
    )

    task = ApiFunction(
        name='pm_task_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'task/index'),
        role_name='pm_task_api_function_role',
        integrations=[HttpIntegration(
            url_path='/task/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_task_api_function_integration'
        )]
    )

    user = ApiFunction(
        name='pm_user_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'user/index'),
        role_name='pm_user_api_function_role',
        integrations=[HttpIntegration(
            url_path='/user',
            methods=[api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_user_api_function_integration'
        )]
    )

    metric = ApiFunction(
        name='pm_metric_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'metric/index'),
        role_name='pm_metric_api_function_role',
        integrations=[HttpIntegration(
            url_path='/metric/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.PATCH, api_gtw.HttpMethod.GET,
                     api_gtw.HttpMethod.OPTIONS],
            name='pm_metric_api_function_integration'
        )]
    )

    tag = ApiFunction(
        name='pm_tag_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path=os.path.join(Common.functions_dir, 'tag/index'),
        role_name='pm_tag_api_function_role',
        integrations=[HttpIntegration(
            url_path='/tag/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_tag_api_function_integration'
        )]
    )
