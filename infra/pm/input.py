import os
from typing import List, Iterable
from aws_cdk import Duration, aws_events as events, aws_apigatewayv2 as api_gtw
from dotenv import load_dotenv

from shared.variables import *

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

    def __init__(self, queue_name: str, visibility_timeout: Duration, max_retries: int = 3,):
        self.name = queue_name
        self.visibility_timeout = visibility_timeout
        self.max_retries = max_retries


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


# --- Common Project Variables ---

class Common:
    root_dir = os.getenv(root_dir)
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
    shared_path = shared_dir
    docker_path = root_dir


    opensearch_port = '443'
    generative_model = 'anthropic.claude-3-sonnet-20240229-v1:0'
    embedding_model = 'amazon.titan-embed-text-v1'



class Vpc:
    stack_name = 'PmVPCStack'
    cidr = '10.0.0.0/16'
    net_prefix = 'pm_vpc'
    secrets_manager_endpoint = 'pm_secretsmanager_endpoint'


class Db:
    stack_name = 'PmDbStack'
    instance_name = 'pm_db'
    sec_group = 'pm_db_sec_group'
    subnet_group = 'pm_db_subnet_group'
    port = 3306
    secret = 'pm_db_secret'
    proxy_name = 'pm-db-proxy'

    initializer_function = CustomResourceTriggeredFunction(
        name='pm_db_initializer_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='schema',
        role_name='pm_db_initializer_func_role',
        trigger=CustomResourceTrigger(resource_name='pm_db_initialization_resource',
                                      provider_name='pm_db_initialization_provider')
    )



class Bastion:
    stack_name = 'PmBastionStack'
    role = 'pm_bastion_role'
    sec_group = 'pm_bastion_sec_group'
    sec_group_ingress_allow_cidr = '0.0.0.0/0'
    sec_group_ingress_allow_port = 22
    ec2_ami = os.getenv(bastion_ami)
    instance_name = 'pm_bastion_host'
    instance_key_name = os.getenv(bastion_instance_key_name)


class Cognito:
    stack_name = 'PmCognitoStack'
    pool_name = 'pm_user_pool'
    client = 'pm_client'
    ver_email_subj = 'Please, verify your email'
    ver_email_body = 'Thanks for signing up! Your verification code is {####}'

    admin_user_creator_function = CustomResourceTriggeredFunction(
        name='pm_cognito_admin_creator_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='cognito',
        role_name='pm_cognito_admin_creator_role',
        trigger=CustomResourceTrigger(
            resource_name='pm_cognito_admin_user_resource',
            provider_name='pm_cognito_admin_user_provider'
        )
    )
    admin_secret_name = 'pm_admin_initial_password'
    admin_tmp_secret_name = 'pm_admin_tmp_password'
    admin_user_name = os.getenv(admin_user)


class Audio:
    stack_name = 'PmAudioStack'
    transcribe_input_bucket_name = 'pm_transcribe_audio_input_bucket'
    transcribe_output_bucket_name = 'pm_transcribe_audio_output_bucket'

    transcribe_in = Function(
        name='pm_audio_processing_transcribe_in',
        timeout=Duration.seconds(30),
        memory_size=1024,
        code_path='audio/transcribe_in',
        role_name='pm_audio_processing_func_role'
    )
    transcribe_out = Function(
        name='pm_audio_processing_transcribe_out',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path='audio/transcribe_out',
        role_name='pm_transcribe_out_function_role'
    )


class Image:
    stack_name = 'PmImageStack'
    bda_input_bucket_name = 'pm_images_input_bucket'
    bda_output_bucket_name = 'pm_bda_image_output_bucket'
    bda_role_name = 'pm_bda_role'
    bda_blueprint_name = 'pm_image_analyzer'
    bda_model_name = Common.generative_model

    bda_in = Function(
        name='pm_image_bda_in',
        timeout=Duration.seconds(30),
        memory_size=1024,
        code_path='image/bda_in',
        role_name='pm_bda_in_function_role'
    )
    bda_out = Function(
        name='pm_image_processing_bda_out',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path='image/bda_out',
        role_name='pm_bda_out_function_role'
    )


class Text:
    stack_name = 'PmTextStack'
    topic_name = 'pm_text_processing_topic'
    generative_model = Common.generative_model
    embedding_model = Common.embedding_model
    max_tokens = '1024'
    domain = 'pm_text_embedding_domain'
    domain_data_nodes = 1
    domain_data_node_instance_type = 't3.small.search'
    domain_ebs_volume_size = 10
    opensearch_index = 'pm_note_text_embedding_opensearch_index'
    opensearch_index_refresh_interval = '30s'
    embedding_vector_dimension = 1536

    metrics_extraction = QueueFunction(
        name='pm_metrics_extraction_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='text/metric',
        role_name='pm_metrics_extraction_role',
        integration=QueueIntegration(queue_name='pm_metrics_extraction_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    links_extraction = QueueFunction(
        name='pm_links_extraction_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='text/link',
        role_name='pm_links_extraction_role',
        integration=QueueIntegration(queue_name='pm_links_extraction_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    tasks_extraction = QueueFunction(
        name='pm_tasks_extraction_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='text/task',
        role_name='pm_tasks_extraction_role',
        integration=QueueIntegration(queue_name='pm_tasks_extraction_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    embedding = QueueFunction(
        name='pm_embedding_func',
        timeout=Duration.minutes(3),
        memory_size=1024,
        code_path='text/embedding',
        role_name='pm_embedding_role',
        integration=QueueIntegration(queue_name='pm_embedding_queue',
                                     visibility_timeout=Duration.minutes(5))
    )
    embedding_index_creator_function = CustomResourceTriggeredFunction(
        name='pm_text_embedding_index_creator_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='opensearch',
        role_name='embedding_index_creator_function_role',
        trigger=CustomResourceTrigger(resource_name='pm_embedding_index_creator_function_resource',
                                      provider_name='pm_embedding_index_creator_function_provider')
    )


class Tagging:
    stack_name = 'PmTaggingStack'
    topic_name = 'pm_tagging_topic'
    model = Common.generative_model
    max_tokens = '1024'

    metric = QueueFunction(
        name='pm_metric_tagging_func',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path='tagging/metric',
        role_name='pm_metric_tagging_role',
        integration=QueueIntegration(queue_name='pm_metric_tagging_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    link = QueueFunction(
        name='pm_link_tagging_func',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path='tagging/link',
        role_name='pm_link_tagging_role',
        integration=QueueIntegration(queue_name='pm_link_tagging_queue',
                                     visibility_timeout=Duration.minutes(2))
    )

    task = QueueFunction(
        name='pm_task_tagging_func',
        timeout=Duration.minutes(1),
        memory_size=2048,
        code_path='tagging/task',
        role_name='pm_task_tagging_role',
        integration=QueueIntegration(queue_name='pm_task_tagging_queue',
                                     visibility_timeout=Duration.minutes(2))
    )


class Recurrent:
    stack_name = 'PmRecurrentStack'
    data_cleanup_function = ScheduledFunction(
        name='pm_db_data_cleanup_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='recurrent/data/purge',
        role_name='pm_db_data_cleanup_func_role',
        schedule_params=Schedule(rule_name='pm_db_data_cleanup_rule',
                                 schedule=events.Schedule.cron(minute='0', hour='0')),
    )

    occurrence_cleanup_function = ScheduledFunction(
        name='pm_db_occurrence_cleanup_func',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='recurrent/occurrence/purge',
        role_name='pm_db_occurrence_cleanup_func_role',
        schedule_params=Schedule(rule_name='pm_db_occurrence_cleanup_rule',
                                 schedule=events.Schedule.cron(minute='0', hour='0')),
    )

    data_generation_function = ScheduledFunction(
        name='pm_db_data_generation_func',
        timeout=Duration.minutes(5),
        memory_size=4096,
        code_path='recurrent/data/generate',
        role_name='pm_db_data_generation_func_role',
        schedule_params=Schedule(rule_name='pm_db_data_generation_rule',
                                 schedule=events.Schedule.cron(minute='*')))

    occurrence_generation_function = ScheduledFunction(
        name='pm_db_occurrence_generation_func',
        timeout=Duration.minutes(5),
        memory_size=4096,
        code_path='recurrent/occurrence/generate',
        role_name='pm_db_occurrence_generation_func_role',
        schedule_params=Schedule(rule_name='pm_db_occurrence_generation_rule',
                                 schedule=events.Schedule.cron(minute='*')))

class Api:
    stack_name = 'PmApiStack'
    name = 'pm_api'
    authorizer = 'pm_authorizer'
    api_url = 'api.predicted.me'

    presign = ApiFunction(
        name='pm_presign_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='presign',
        role_name='pm_presign_function_role', integrations=[HttpIntegration(
            url_path='/presign',
            methods=[api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_presign_function_integration')]
    )

    note = ApiFunction(
        name='pm_note_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='note',
        role_name='pm_note_api_function_role',
        integrations=[HttpIntegration(
            url_path='/note/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_note_api_function_integration'
        )]
    )
    # todo add this path param to path and delete
    data = ApiFunction(
        name='pm_data_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='data',
        role_name='pm_data_api_function_role',
        integrations=[HttpIntegration(
            url_path='/metric/{id}/data',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.OPTIONS],
            name='pm_data_api_function_integration'
        ),
            HttpIntegration(
                url_path='/data/{id}',
                methods=[api_gtw.HttpMethod.GET, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                         api_gtw.HttpMethod.OPTIONS],
                name='pm_data_api_function_integration'
            )
        ]
    )

    occurrence = ApiFunction(
        name='pm_occurrence_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='occurrence',
        role_name='pm_occurrence_api_function_role',
        integrations=[HttpIntegration(
            url_path='/task/{id}/occurrence',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.OPTIONS],
            name='pm_occurrence_api_function_integration'
        ),
            HttpIntegration(
                url_path='/occurrence/{id}',
                methods=[api_gtw.HttpMethod.GET, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                         api_gtw.HttpMethod.OPTIONS],
                name='pm_occurrence_api_function_integration'
            )
        ]
    )

    link = ApiFunction(
        name='pm_link_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='link',
        role_name='pm_link_api_function_role',
        integrations=[HttpIntegration(
            url_path='/link/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_link_api_function_integration'
        )]
    )

    metric_schedule = ApiFunction(
        name='pm_metric_schedule_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='schedule/metric',
        role_name='pm_metric_schedule_api_function_role',
        integrations=[HttpIntegration(
            url_path='/metric/schedule/{id}',
            methods=[api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.OPTIONS],
            name='pm_task_schedule_api_function_integration'
        ),
            HttpIntegration(
                url_path='/metric/{id}/schedule',
                methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.OPTIONS],
                name='pm_task_schedule_api_function_integration'
            )]
    )

    task_schedule = ApiFunction(
        name='pm_task_schedule_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='schedule/task',
        role_name='pm_task_schedule_api_function_role',
        integrations=[HttpIntegration(
            url_path='/task/schedule/{id}',
            methods=[api_gtw.HttpMethod.DELETE, api_gtw.HttpMethod.PATCH,
                     api_gtw.HttpMethod.OPTIONS],
            name='pm_task_schedule_api_function_integration'
        ),
            HttpIntegration(
                url_path='/task/{id}/schedule',
                methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.OPTIONS],
                name='pm_task_schedule_api_function_integration'
            )
        ]
    )

    task = ApiFunction(
        name='pm_task_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='task',
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
        code_path='user',
        role_name='pm_user_api_function_role',
        integrations=[HttpIntegration(
            url_path='/user',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_user_api_function_integration'
        )]
    )

    metric = ApiFunction(
        name='pm_metric_api_function',
        timeout=Duration.minutes(1),
        memory_size=1024,
        code_path='metric',
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
        code_path='tag',
        role_name='pm_tag_api_function_role',
        integrations=[HttpIntegration(
            url_path='/tag/{id}',
            methods=[api_gtw.HttpMethod.POST, api_gtw.HttpMethod.GET, api_gtw.HttpMethod.OPTIONS],
            name='pm_tag_api_function_integration'
        )]
    )

