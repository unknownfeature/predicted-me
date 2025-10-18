import json
import os
import traceback
from typing import Dict, Any
from urllib.parse import unquote_plus

import boto3
from sqlalchemy.orm import Session

from shared import constants
from shared.variables import *

s3_client = boto3.client(constants.s3)
sns_client = boto3.client(constants.sns)

from backend.lib.db import Note, Origin, begin_session
from sqlalchemy import select

output_bucket_name = os.getenv(transcribe_bucket_out)
text_topic_arn = os.getenv(text_processing_topic_arn)

def get_note_id_from_transcribe_job(job_name: str, session: Session) -> int | None:
        note_query = select(Note).where(Note.audio_key == job_name)
        target_note = session.scalar(note_query)
        return target_note.id


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    session = begin_session()

    try:
        record = event[constants.records][0]
        output_key = unquote_plus(record[constants.s3][constants.object][constants.s3_key])

        transcript_json = read_job_result_json(output_key)

        job_name = transcript_json[constants.job_name]
        transcript_text = transcript_json[constants.results][constants.transcripts][0][constants.transcript]

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

        send_to_sns(note_id)


        return {constants.status: constants.success, constants.note_id: note_id}

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return {constants.status: constants.error, constants.error: str(e)}

    finally:
        session.close()


def read_job_result_json(key: str) -> Dict[str, Any]:
    return json.loads(s3_client.get_object(Bucket=output_bucket_name, Key=key)[constants.s3_body].read())


def send_to_sns(note_id: int):
    sns_payload = {
        constants.note_id: note_id,
        constants.origin: Origin.audio_text.value,
    }
    sns_client.publish(
        TopicArn=text_topic_arn,
        Message=json.dumps(sns_payload),
        Subject=f"Audio Transcript Ready for Metrics Extraction: {note_id}"
    )