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

from backend.lib.db import Note, Origin, begin_session
from sqlalchemy import select, update

output_bucket_name = os.getenv(Env.transcribe_bucket_out)
text_topic_arn = os.getenv(Env.text_processing_topic_arn)

def get_note_id_from_transcribe_job(job_name: str, session: Any) -> int | None:
        note_query = select(Note).where(Note.image_key == job_name)
        target_note = session.execute(note_query).first()
        return target_note.id


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = begin_session()

    try:
        record = event['Records'][0]
        output_key = unquote_plus(record['s3']['object']['key'])

        s3_response = s3_client.get_object(Bucket=output_bucket_name, Key=output_key)
        transcript_json = json.loads(s3_response['Body'].read())

        job_name = transcript_json['jobName']
        transcript_text = transcript_json['results']['transcripts'][0]['transcript']

        note_id = get_note_id_from_transcribe_job(job_name, session)

        if not note_id:
            raise ValueError(f"Could not correlate job {job_name} back to a Note ID.")

        target_note = session.get(Note, note_id)
        if not target_note:
            raise ValueError(f"Note ID {note_id} not found for update.")

        target_note.audio_text = transcript_text
        target_note.audio_transcribed = True
        session.add(target_note)

        session.commit()
        logger.info(f"Successfully transcribed and updated Note ID {note_id}.")

        sns_payload = {
            'note_id': note_id,
            'origin': Origin.audio_text.value,
        }

        sns_client.publish(
            TopicArn=text_topic_arn,
            Note=json.dumps(sns_payload),
            Subject=f"Audio Transcript Ready for Metrics Extraction: {note_id}"
        )

        logger.info(f"Published SNS notification for metrics extraction.")

        return {'statusCode': 200, 'note_id': note_id}

    except Exception as e:
        session.rollback()
        logger.error(f"FATAL ERROR processing transcript: {e}")
        raise

    finally:
        session.close()