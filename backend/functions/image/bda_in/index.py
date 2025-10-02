import os
import json

import boto3

from shared.variables import Common, Env

bda_client = boto3.client(
    service_name='bedrock-data-automation',
    region_name=os.getenv(Env.aws_region, Common.default_region)
)

output_bucket = os.getenv(Env.bda_output_bucket_name)
job_execution_role = os.getenv(Env.bda_job_execution_role_arn)
blueprint_name = os.getenv(Env.bda_blueprint_name)
bda_model_name = os.getenv(Env.bda_model_name)


def handler(event, context):
    try:
        record = event['Records'][0]
        input_bucket = record['s3']['bucket']['name']
        input_key = record['s3']['object']['key']

        input_s3_uri = f"s3://{input_bucket}/{input_key}"
        output_s3_uri = f"s3://{output_bucket}/{input_key}/"

        response = bda_client.start_data_automation_job(
            jobName=f"image-analysis-{context.aws_request_id}",
            executionRoleArn=job_execution_role,
            inputDataConfig={
                's3Uri': input_s3_uri
            },
            outputDataConfig={
                's3Uri': output_s3_uri
            },
            blueprintName=blueprint_name,
            modelIdentifier=bda_model_name
        )

        print(f"BDA Job started successfully. Job ID: {response['jobId']}")

        return {'statusCode': 200, 'body': json.dumps({'jobId': response['jobId']})}

    except Exception as e:
        print(f"Error during BDA job orchestration: {e}")
        return {'statusCode': 500, 'body': f'Error starting BDA job: {e}'}
