import os
import json
import traceback

import boto3
from backend.lib import constants
from shared.variables import Common, Env

bda_client = boto3.client(
    service_name=constants.bda,
    region_name=os.getenv(Env.aws_region, Common.default_region)
)

output_bucket = os.getenv(Env.bda_output_bucket_name)
job_execution_role = os.getenv(Env.bda_job_execution_role_arn)
blueprint_name = os.getenv(Env.bda_blueprint_name)
bda_model_name = os.getenv(Env.bda_model_name)


def handler(event, _):
    try:
        record = event[constants.records][0]
        input_bucket = record[constants.s3][constants.bucket][constants.name]
        input_key = record[constants.s3][constants.object][constants.key]

        input_s3_uri = f's3://{input_bucket}/{input_key}'
        output_s3_uri = f's3://{output_bucket}/{input_key}/'

        start_bda_job(input_key, input_s3_uri, output_s3_uri)


        return {constants.status: constants.success}

    except Exception as e:
        traceback.print_exc()
        return  {constants.status: constants.error, constants.error: str(e)}


def start_bda_job(input_key: str, input_s3_uri: str, output_s3_uri: str):
    bda_client.start_data_automation_job(
        jobName=input_key,
        executionRoleArn=job_execution_role,
        inputDataConfig={
            constants.s3_uri: input_s3_uri
        },
        outputDataConfig={
            constants.s3_uri: output_s3_uri
        },
        blueprintName=blueprint_name,
        modelIdentifier=bda_model_name
    )
