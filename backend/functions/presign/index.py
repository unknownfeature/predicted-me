import json
import os
import traceback
import uuid
from typing import Dict, Any

import boto3

from backend.lib import constants
from shared.variables import Env, Common

s3_client = boto3.client(constants.s3)
images_bucket = os.getenv(Env.bda_input_bucket_name)
audio_bucket = os.getenv(Env.transcribe_bucket_in)

content_type_resolver = {
    constants.mp4: 'audio/mp4',
    constants.heic: 'image/heic',
    constants.jpg: 'image/jpeg',
    constants.png: 'image/png',
    constants.jpeg: 'image/jpeg'
}

s3_method_resolver = {
    constants.put: 'put_object',
    constants.get: 'get_object',
    constants.delete: 'delete_object',
}


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    try:
        if event[constants.http_method] != constants.get:
            return {
                constants.status_code: 405,
                constants.headers: Common.cors_headers,
                constants.body: json.dumps('Method Not Allowed')
            }

        query_params = event.get(constants.query_params) or {}
        extension = query_params.get(constants.extension)
        content_type = content_type_resolver.get(extension)
        method = query_params.get(constants.method).lower() #may it fail if it's not there, that's what it should do
        s3_method = s3_method_resolver[method]
        bucket = images_bucket if extension != constants.mp4 else audio_bucket
        key = f'{ uuid.uuid4().hex}.{extension}'

        presigned_url = generate_presigned_url(bucket, content_type, key, s3_method)

        return {
            constants.status_code: 200,
            constants.headers: Common.cors_headers,
            constants.body: json.dumps({constants.url: presigned_url, constants.key: key})
        }

    except Exception as e:
        traceback.print_exc()
        return {
            constants.status_code: 500,
            constants.headers: Common.cors_headers,
            constants.body: json.dumps(f'Error generating presigned URL. {str(e)}')
        }


def generate_presigned_url(bucket: str, content_type: str, key: str, s3_method: str) -> str:
    presigned_url = s3_client.generate_presigned_url(
        s3_method,
        Params={
            constants.bucket: bucket,
            constants.key: key,
            constants.content_type: content_type,
        },
        ExpiresIn=300
    )
    return presigned_url
