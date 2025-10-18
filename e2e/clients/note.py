import os
from typing import Dict, Any

from e2e.clients import api
from e2e.common import base_url, build_query_string
from e2e.s3 import stream_s3_to_presigned_url
from shared import constants

note_path = base_url + '/note'

image_bucket = os.getenv('IMAGE_BUCKET')
audio_bucket = os.getenv('AUDIO_BUCKET')


def create(jwt: str, text: str = None, audio_s3_source: str = None, image_s3_source: str = None, ) -> int:
    audio_key = stream_s3_to_presigned_url(audio_bucket, audio_s3_source, jwt) if audio_s3_source else None
    image_key = stream_s3_to_presigned_url(image_bucket, image_s3_source, jwt) if image_s3_source else None
    return api.create(
        note_path, {
            constants.text: text,
            constants.audio_key: audio_key,
            constants.image_key: image_key,
        }, jwt)


def get(note_id: int, jwt: str, query_params: Dict[str, str] = {}, ) -> Dict[str, Any]:
    return api.get(note_path + f'/{note_id}?{build_query_string(query_params)}', jwt)
