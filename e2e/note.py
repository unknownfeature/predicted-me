import os
from typing import Dict, Any

import boto3

from common import base_url, get_headers

import requests

from e2e.s3 import stream_s3_to_presigned_url

note_path = base_url + '/note'



image_bucket = os.getenv('IMAGE_BUCKET')
audio_bucket = os.getenv('AUDIO_BUCKET')



def create_note(text: str, audio_s3_source: str, image_s3_source: str, jwt: str) -> int:

    audio_key = stream_s3_to_presigned_url(audio_bucket, audio_s3_source, jwt) if audio_s3_source else None
    image_key = stream_s3_to_presigned_url(image_bucket, image_s3_source, jwt) if image_s3_source else None
    resp = requests.post(note_path, headers=get_headers(jwt), json={
        'text': text,
        'audio_key': audio_key,
        'image_key': image_key,
    })

    assert resp.ok()
    return resp.json()['id']


def get_note(note_id: int, query_params: Dict[str, str], jwt: str) -> Dict[str, Any]:
    pass
