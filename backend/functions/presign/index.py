import json
import os
import traceback
import uuid
from typing import Dict, Any
import mimetypes

import boto3

from shared.variables import *
from shared import constants

s3_client = boto3.client(constants.s3)
images_bucket = os.getenv(bda_input_bucket_name)
audio_bucket = os.getenv(transcribe_bucket_in)

default_content_type = 'binary/octet-stream'


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    try:
        if event[constants.http_method] != constants.get:
            return {
                constants.status_code: 405,
                constants.headers: constants.cors_headers,
                constants.body: json.dumps('Method Not Allowed')
            }

        query_params = event.get(constants.query_params)

        extension = query_params.get(constants.extension)
        key = query_params.get(constants.key)
        method = query_params[constants.method].lower()  # may it fail if it's not there, that's what it should do
        if method == constants.put.lower():
            if not extension:
                raise Exception('extension must be specified')
            key = f'{generate_key()}.{extension}'
            bucket, content_type = get_bucket_and_content_type(key)
            presigned_url = generate_presigned_url(bucket, content_type, key, 'put_object')
        elif method == constants.get.lower():
            if not key:
                raise Exception('key must be specified')
            bucket, content_type = get_bucket_and_content_type(key)
            presigned_url = generate_presigned_url(bucket, content_type, key, 'get_object')
        else:
            return {
                constants.status_code: 400,
                constants.headers: constants.cors_headers,
                constants.body: json.dumps(f'unsupported method {method}')
            }

        return {
            constants.status_code: 200,
            constants.headers: constants.cors_headers,
            constants.body: json.dumps(
                {constants.url: presigned_url, constants.key: key, constants.content_type: content_type})
        }

    except Exception as e:
        traceback.print_exc()
        return {
            constants.status_code: 500,
            constants.headers: constants.cors_headers,
            constants.body: json.dumps(f'Error generating presigned URL. {str(e)}')
        }


def get_bucket_and_content_type(key):
    content_type, _ = mimetypes.guess_type(key)
    if not content_type:
        content_type = default_content_type
    bucket = audio_bucket if content_type.startswith('audio') else images_bucket  if content_type.startswith('image') else None
    if not bucket:
        raise Exception('content not supported')
    return bucket, content_type

def generate_key():
    return uuid.uuid4().hex



def generate_presigned_url(bucket: str, content_type: str, key: str, s3_method: str) -> str:
    presigned_url = s3_client.generate_presigned_url(
        s3_method,
        Params={
            constants.bucket: bucket,
            constants.s3_key: key,
            constants.content_type: content_type,
        },
        ExpiresIn=300  # move this to env variables todo
    )
    return presigned_url
