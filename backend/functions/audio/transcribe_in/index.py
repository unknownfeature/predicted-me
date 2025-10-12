import os
import traceback
from typing import Dict, Any
from urllib.parse import unquote_plus

import boto3

from backend.lib import constants
from shared.variables import Env

s3_client = boto3.client(constants.s3)
transcribe_client = boto3.client(constants.transcribe)

input_bucket_name = os.environ.get(Env.transcribe_bucket_in)
output_bucket_name = os.environ.get(Env.transcribe_bucket_out)


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    try:
        record = event[constants.records][0]
        input_key = unquote_plus(record[constants.s3][constants.object][constamts.s3_key], encoding=constants.utf_8)

        file_uri = f's3://{input_bucket_name}/{input_key}'
        media_format = input_key.split('.')[-1].upper()

        start_transcription_job(file_uri, input_key, media_format)

        return {constants.status: constants.success}

    except Exception as e:
        traceback.print_exc()
        return {constants.status: constants.error, constants.error: str(e)}


def start_transcription_job(file_uri: str, input_key: str, media_format: str):
    transcribe_client.start_transcription_job(
        TranscriptionJobName=input_key,
        LanguageCode='en-US',  # todo add ability to select language (in distant future)
        Media={constants.media_file_uri: file_uri, constants.media_format: media_format},
        OutputBucketName=output_bucket_name,
        OutputKey=input_key
    )
