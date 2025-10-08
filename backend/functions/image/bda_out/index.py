import json
import os
import re
import traceback
from urllib.parse import unquote_plus

import boto3
from sqlalchemy import select, update

from backend.lib.db import Note, Origin, begin_session
from shared.variables import Env

s3_client = boto3.client(constants.s3)
sns_client = boto3.client(constants.sns)
sns_topic_arn = os.getenv(Env.text_processing_topic_arn)

#  maybe pass blueprint attributes via env too todo


def process_output_file(bucket, key):
    s3_response = s3_client.get_object(Bucket=bucket, Key=key)
    file_content = s3_response[constants.Body].read().decode('utf-8')

    return [json.loads(line) for line in file_content.strip().split('\n') if line]


def handler(event, context):
    try:
        record = event[constants.Records][0]
        bucket_name = record[constants.s3][constants.bucket][constants.name]
        object_key = unquote_plus(record[constants.s3][constants.object][constants.key])
        image_key_uuid_str = extract_uuid_from_key(object_key)


    except Exception as e:
        print(f"Error during key extraction/parsing: {e}")
        traceback.print_exc()
        return {constants.statusCode: 400, constants.body: 'Invalid S3 key structure or missing UUID.'}

    image_descriptions = process_output_file(bucket_name, object_key)

    if not image_descriptions:
        print(f"No valid inference results found for key {image_key_uuid_str}.")
        return {constants.statusCode: 200, constants.body: 'No data to write.'}

    session = begin_session()

    desc_data = image_descriptions[0].get(constants.inference_result, {})

    image_description = desc_data.get(constants.image_description)
    image_text = desc_data.get(constants.image_text)
    try:

        note_query = select(Note).where(Note.image_key == image_key_uuid_str)
        target_note = session.execute(note_query).first()
        note_id = target_note.id

        update_note_stmt = (
            update(Note)
            .where(Note.id == note_id)
            .values(
                image_description=image_description,
                image_text=image_text,
                image_described=True
            )
        )
        session.execute(update_note_stmt)
        print(f"Updated Note ID {image_key_uuid_str} with main description.")

        session.commit()

        send_text_to_sns(image_description, note_id, Origin.img_desc.value)
        send_text_to_sns(image_text, note_id, Origin.img_text.value)


    except Exception as e:
        session.rollback()
        print(f"Database transaction failed: {e}")
        traceback.print_exc()
        #  todo handle error
        return {constants.statusCode: 500, constants.body: f"Couldn't process output due to the error: {traceback.format_exc()}."}

    finally:
        session.close()

    return {constants.statusCode: 200,
            constants.body: f"Processed output and potentially triggered tagging for Note ID {note_id}."}


def send_text_to_sns(image_description, note_id, origin):
    if image_description:
        sns_payload = {
            constants.note_id: note_id,
            constants.origin: origin
        }

        sns_client.publish(
            TopicArn=sns_topic_arn,
            Note=json.dumps(sns_payload),
            Subject='Text ready for metrics extraction for Note ID {note_id} and origin {origin}.'
        )

        print(f"Sent SNS note for final categorization of Note ID {note_id}.")


def extract_uuid_from_key(object_key: str) -> str:
    # Example input: 'a1b2c3d4-..../job-12345678/output.jsonl'

    parts = object_key.split('/')

    if parts and re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', parts[0], re.I):
        return parts[0]

    raise ValueError(f"Could not find a valid UUID in the expected prefix of the S3 key: {object_key}")

