import json
import os
import traceback
from typing import List, Dict, Any
from urllib.parse import unquote_plus

import boto3
from sqlalchemy import select

from shared import constants
from backend.lib.db import Note, Origin, begin_session
from shared.variables import *

s3_client = boto3.client(constants.s3)
sns_client = boto3.client(constants.sns)
sns_topic_arn = os.getenv(text_processing_topic_arn)


def read_data_from_output_file(bucket: str, key: str) -> List[Dict[str, Any]]:
    s3_response = s3_client.get_object(Bucket=bucket, Key=key)
    file_content = s3_response[constants.s3_body].read().decode('utf-8')

    return [json.loads(line) for line in file_content.strip().split('\n') if line]


def handler(event, _):
    session = begin_session()
    try:
        record = event[constants.records][0]
        bucket_name = record[constants.s3][constants.bucket][constants.name]
        object_key = unquote_plus(record[constants.s3][constants.object][constants.s3_key])

        image_descriptions = read_data_from_output_file(bucket_name, object_key)

        if not image_descriptions:
            return {constants.status: constants.error, constants.error: f'No valid inference results found for key {object_key}.'}

        session = begin_session()

        desc_data = image_descriptions[0].get(constants.inference_result, {})

        image_description = desc_data.get(constants.image_description)
        image_text = desc_data.get(constants.image_text)


        note_query = select(Note).where(Note.image_key == object_key)
        target_note = session.scalar(note_query)
        target_note.image_text = image_text
        target_note.image_description = image_description
        target_note.image_described = True

        note_id = target_note.id
        session.add(target_note)

        session.commit()

        send_text_to_sns(image_description, note_id, Origin.img_desc.value)
        send_text_to_sns(image_text, note_id, Origin.img_text.value)

    except Exception as e:
        traceback.print_exc()
        return {constants.status: constants.error, constants.error: str(e)}
    finally:
        session.close()

    return {constants.status: constants.success}



def send_text_to_sns(image_description: str, note_id: int, origin: str):
    if image_description:
        sns_payload = {
            constants.note_id: note_id,
            constants.origin: origin
        }

        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(sns_payload),
            Subject='Text ready for metrics extraction for Note ID {note_id} and origin {origin}.'
        )

        print(f"Sent SNS note for final categorization of Note ID {note_id}.")

