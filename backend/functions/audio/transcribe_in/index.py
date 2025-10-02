import logging
import os
from typing import Dict, Any
from urllib.parse import unquote_plus

import boto3

from shared.variables import Env

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

input_bucket_name = os.environ.get(Env.transcribe_bucket_in)
output_bucket_name = os.environ.get(Env.transcribe_bucket_out)



def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:

    try:
        record = event['Records'][0]
        input_key = unquote_plus(record['s3']['object']['key'])


        file_uri = f"s3://{input_bucket_name}/{input_key}"
        media_format = input_key.split('.')[-1].upper()

        transcribe_client.start_transcription_job(
            TranscriptionJobName=input_key,
            LanguageCode='en-US', # todo add ability to select language (in distant future)
            Media={'MediaFileUri': file_uri, 'MediaFormat': media_format},
            OutputBucketName=output_bucket_name,
            OutputKey= f'{input_key}.json'
        )

        return {'statusCode': 200, 'job_name': input_key, 'file_key': input_key}

    except Exception as e:
        logger.error(f"Error starting Transcribe job for {input_key}: {e}")
        raise