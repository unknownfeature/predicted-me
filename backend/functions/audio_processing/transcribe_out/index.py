import os
import json
import boto3
from urllib.parse import unquote_plus
import logging
from typing import Dict, Any

from shared.variables import Env

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

from backend.lib.db.mapping import Message, MetricOrigin
from backend.lib.db.util import begin_session
from sqlalchemy import select, update

output_bucket_name = os.getenv(Env.transcribe_bucket_out)
text_topic_arn = os.getenv(Env.text_processing_topic_arn)

def get_message_id_from_transcribe_job(job_name: str, session: Any) -> int | None:
        message_query = select(Message).where(Message.image_key == job_name)
        target_message = session.scalar(message_query)
        return target_message.id


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = begin_session()

    try:
        record = event['Records'][0]
        output_key = unquote_plus(record['s3']['object']['key'])

        s3_response = s3_client.get_object(Bucket=output_bucket_name, Key=output_key)
        transcript_json = json.loads(s3_response['Body'].read())

        job_name = transcript_json['jobName']
        transcript_text = transcript_json['results']['transcripts'][0]['transcript']

        message_id = get_message_id_from_transcribe_job(job_name, session)

        if not message_id:
            raise ValueError(f"Could not correlate job {job_name} back to a Message ID.")

        target_message = session.get(Message, message_id)
        if not target_message:
            raise ValueError(f"Message ID {message_id} not found for update.")

        target_message.audio_text = transcript_text
        target_message.audio_transcribed = True
        session.add(target_message)

        session.commit()
        logger.info(f"Successfully transcribed and updated Message ID {message_id}.")

        sns_payload = {
            'message_id': message_id,
            'origin': MetricOrigin.audio.value,
        }

        sns_client.publish(
            TopicArn=text_topic_arn,
            Message=json.dumps(sns_payload),
            Subject=f"Audio Transcript Ready for Metrics Extraction: {message_id}"
        )

        logger.info(f"Published SNS notification for metrics extraction.")

        return {'statusCode': 200, 'message_id': message_id}

    except Exception as e:
        session.rollback()
        logger.error(f"FATAL ERROR processing transcript: {e}")
        raise

    finally:
        session.close()