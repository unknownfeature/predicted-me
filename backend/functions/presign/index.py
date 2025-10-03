import json
import os
import traceback
import uuid
from typing import Dict, Any

import boto3

from shared.variables import Env, Common

s3_client = boto3.client('s3')
images_bucket = os.getenv(Env.bda_input_bucket_name)
audio_bucket = os.getenv(Env.transcribe_bucket_in)

content_type_resolver = {
    'mp4': 'audio/mp4',
    'heic': 'image/heic',
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'jpeg': 'image/jpeg'
}

s3_method_resolver = {
    'put': 'put_object',
    'get': 'get_object',
    'delete': 'delete_object',
}


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    try:
        if event['httpMethod'] != 'GET':
            return {
                'statusCode': 405,
                'headers': Common.cors_headers,
                'body': json.dumps('Method Not Allowed')
            }

        query_params = event.get('queryStringParameters') or {}
        extension = query_params.get('extension')
        content_type = content_type_resolver.get(extension)
        method = query_params.get('method').lower() #may it fail if it's not there, that's what it should do
        s3_method = s3_method_resolver[method]
        bucket = images_bucket if extension != 'mp4' else audio_bucket
        key = f'{ uuid.uuid4().hex}.{extension}'

        presigned_url = s3_client.generate_presigned_url(
            s3_method,
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': content_type,
            },
            ExpiresIn=300
        )

        return {
            'statusCode': 200,
            'headers': Common.cors_headers,
            'body': json.dumps({'url': presigned_url, 'key': key})
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': Common.cors_headers,
            'body': json.dumps(f'Error generating presigned URL. {str(e)}')
        }
