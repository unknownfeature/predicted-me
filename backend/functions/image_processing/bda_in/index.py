import os
import json
import re

import boto3

bda_client = boto3.client(
    service_name='bedrock-data-automation',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET_NAME']
JOB_EXECUTION_ROLE = os.environ['JOB_EXECUTION_ROLE_ARN']
BLUEPRINT_NAME = os.environ['BLUEPRINT_NAME']
BDA_MODEL_NAME = os.environ['BDA_MODEL_NAME']


def handler(event, context):
    try:
        record = event['Records'][0]
        input_bucket = record['s3']['bucket']['name']
        input_key = record['s3']['object']['key']

        input_s3_uri = f"s3://{input_bucket}/{input_key}"
        output_s3_uri = f"s3://{OUTPUT_BUCKET}/{input_key}/"

        response = bda_client.start_data_automation_job(
            jobName=f"image-analysis-{context.aws_request_id}",
            executionRoleArn=JOB_EXECUTION_ROLE,
            inputDataConfig={
                's3Uri': input_s3_uri
            },
            outputDataConfig={
                's3Uri': output_s3_uri
            },
            blueprintName=BLUEPRINT_NAME,
            modelIdentifier=BDA_MODEL_NAME
        )

        print(f"BDA Job started successfully. Job ID: {response['jobId']}")

        return {'statusCode': 200, 'body': json.dumps({'jobId': response['jobId']})}

    except Exception as e:
        print(f"Error during BDA job orchestration: {e}")
        return {'statusCode': 500, 'body': f'Error starting BDA job: {e}'}
