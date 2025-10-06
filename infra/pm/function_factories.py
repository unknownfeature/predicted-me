from typing import Dict, Sequence, Callable, Iterable

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as lmbd,
    aws_sqs as sqs,
    aws_rds as rds,
    aws_lambda_event_sources as lmes,
    aws_apigatewayv2 as api_gtw,
    aws_apigatewayv2_integrations as api_gtw_int,
    aws_s3_notifications as s3n,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_events_targets as targets,
    aws_events as events,
    custom_resources as cr,
    aws_iam as iam)

from shared.variables import Function, ApiFunction, ScheduledFunction, CustomResourceTriggeredFunction


class S3EventParams:
    bucket: s3.Bucket
    event_type: s3.EventType

    def __init__(self, bucket: s3.Bucket, event_type: s3.EventType):
        self.bucket = bucket
        self.event_type = event_type


class FunctionFactoryParams:
    function_params: Function
    build_args: Dict[str, str]
    environment: Dict[str, str]
    role_supplier: Callable[[Stack, Function], iam.Role]
    and_then: Callable[[lmbd.Function], None]
    vpc: ec2.Vpc

    def __init__(self, function_params: Function, build_args: Dict[str, str], environment: Dict[str, str],
                 role_supplier: Callable[[Stack, Function], iam.Role], and_then: Callable[[lmbd.Function], None], vpc: ec2.Vpc = None):
        self.function_params = function_params
        self.build_args = build_args
        self.environment = environment
        self.role_supplier = role_supplier
        self.and_then = and_then
        self.vpc = vpc


def integration_factory(integration_cb: Callable[[lmbd.IFunction], None],
                        and_then: Callable[[lmbd.Function], None]) -> Callable[[lmbd.IFunction], None]:
    def integrate(func: lmbd.Function):
        if not integration_cb:
            return func

        integration_cb(func)

        if and_then:
            and_then(func)

    return integrate


def http_api_integration_cb_factory(api: api_gtw.HttpApi, api_function: ApiFunction) -> Callable[[lmbd.Function], None]:
    def cb(func: lmbd.IFunction):
        if not api_function.integrations:
            return
        for ip in api_function.integrations:
            api.add_routes(path=ip.url_path, methods=ip.methods,
                           integration=api_gtw_int.HttpLambdaIntegration(ip.name, func))

    return cb



def s3_integration_cb_factory(integration_params: Iterable[S3EventParams]) -> Callable[[lmbd.Function], None]:
    def cb(func: lmbd.IFunction):
        if not integration_params:
            return
        for ip in integration_params:
            ip.bucket.grant_read(func)
            ip.bucket.add_event_notification(
                ip.event_type,
                s3n.LambdaDestination(func)
            )

    return cb


def sqs_integration_cb_factory(queues: Sequence[sqs.Queue]) -> Callable[[lmbd.Function], None]:
    def cb(func: lmbd.IFunction):
        if not queues:
            return
        for q in queues:
            q.grant_consume_messages(func)
            func.add_event_source(
                lmes.SqsEventSource(q)
            )

    return cb


def schedule_cb_factory(stack: Stack, scheduled_function: ScheduledFunction) -> Callable[[lmbd.Function], None]:
    def cb(func: lmbd.IFunction):

        daily_rule = events.Rule(stack, scheduled_function.schedule_params.rule_name,
                                 schedule=scheduled_function.schedule_params.schedule)

        daily_rule.add_target(targets.LambdaFunction(func))


    return cb


def custom_resource_trigger_cb_factory(stack: Stack, properties: Dict[str, str],
                                      custom_resource_triggered_function: CustomResourceTriggeredFunction) -> Callable[
    [lmbd.Function], None]:
    def cb(func: lmbd.IFunction):
        provider = cr.Provider(stack, custom_resource_triggered_function.trigger.provider_name, on_event_handler=func)
        cdk.CustomResource(stack, custom_resource_triggered_function.trigger.resource_name,
                           service_token=provider.service_token,
                           properties=properties)

    return cb




def create_lambda_role(stack: Stack, role_name: str, and_then: Callable[[iam.Role], None]):
    role = iam.Role(
        stack, role_name,
        assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        ]
    )

    role.add_to_policy(
        iam.PolicyStatement(
            actions=['ec2:CreateNetworkInterface', 'ec2:DescribeNetworkInterfaces', 'ec2:DeleteNetworkInterface'],
            resources=['*'],
            effect=iam.Effect.ALLOW
        )
    )
    if and_then:
        and_then(role)

    return role



def add_db_access_to_role_cb_factory(db_secret: rds.DatabaseSecret, and_then: Callable[[iam.Role], None] = None) -> Callable[[iam.Role], None]:
     def on_role(role: iam.Role):
        db_secret.grant_read(role)
        if and_then:
            and_then(role)

     return on_role


def create_role_with_db_access_factory(db_secret: rds.DatabaseSecret, and_then: Callable[[iam.Role], None] = None) -> Callable[
    [Stack, Function], iam.Role]:
    return create_function_role_factory(add_db_access_to_role_cb_factory(db_secret, and_then))


def create_function_role_factory(on_role: Callable[[iam.Role], None]) -> Callable[
    [Stack, Function], iam.Role]:
    return lambda stack, params: create_lambda_role(stack, params.role_name, on_role)


def function_with_db_access_cb_factory(db_instance:rds.DatabaseInstance, and_then: Callable[[lmbd.Function], None]) -> Callable[[lmbd.Function], None]:
    def cb(func: lmbd.Function):
        db_instance.connections.allow_default_port_from(func)
        if and_then:
            and_then(func)
    return cb


