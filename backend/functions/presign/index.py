import json
import os
import traceback
import uuid
from typing import Dict, Any

import boto3

from backend.lib import constants
from shared.variables import Env, cors_headers

s3_client = boto3.client(constants.s3)
images_bucket = os.getenv(Env.bda_input_bucket_name)
audio_bucket = os.getenv(Env.transcribe_bucket_in)

content_type_resolver = {
    constants.mp4: 'audio/mp4',
    constants.m4a: 'audio/mp4',
    constants.heic: 'image/heic',
    constants.jpg: 'image/jpeg',
    constants.png: 'image/png',
    constants.jpeg: 'image/jpeg'
}

audio_extensions = { constants.mp4, constants.m4a }

s3_method_resolver = {
    constants.put.lower(): 'put_object',
    constants.get.lower(): 'get_object',
    constants.delete.lower(): 'delete_object',
}


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    try:
        if event[constants.http_method] != constants.get:
            return {
                constants.status_code: 405,
                constants.headers: cors_headers,
                constants.body: json.dumps('Method Not Allowed')
            }

        query_params = event.get(constants.query_params)

        extension = query_params.get(constants.extension)
        key = query_params.get(constants.key)

        content_type = content_type_resolver[extension]

        method = query_params[constants.method] #may it fail if it's not there, that's what it should do
        if method.lower() ==  constants.put.lower():
              if not extension:
                  raise Exception('extension must be specified')
              bucket = images_bucket if extension not in audio_extensions else audio_bucket
              key = f'{generate_key()}.{extension}'

              presigned_url = generate_presigned_url(bucket, content_type, key, 'put_object')
        else:
            if not key:
                raise Exception('key must be specified')
            extension = extension if extension in audio_extensions else get_extension(key)
            presigned_url = generate_presigned_url(get_bucket(extension), content_type, key, get_s3_method(method.lower()))

        return {
            constants.status_code: 200,
            constants.headers: cors_headers,
            constants.body: json.dumps({constants.url: presigned_url, constants.key: key, constants.content_type: content_type})
        }

    except Exception as e:
        traceback.print_exc()
        return {
            constants.status_code: 500,
            constants.headers: cors_headers,
            constants.body: json.dumps(f'Error generating presigned URL. {str(e)}')
        }


def get_extension(key):
    return key[key.rindex('.'):]


def generate_key():
    return uuid.uuid4().hex

def get_s3_method(http_method_lower: str) -> str:
    return s3_method_resolver[http_method_lower]

def get_bucket(extension: str) -> str:
    return images_bucket if extension not in audio_extensions else audio_bucket

def generate_presigned_url(bucket: str, content_type: str, key: str, s3_method: str) -> str:
    presigned_url = s3_client.generate_presigned_url(
        s3_method,
        Params={
            constants.bucket: bucket,
            constants.s3_key: key,
            constants.content_type: content_type,
        },
        ExpiresIn=300 # move this to env variables todo
    )
    return presigned_url
