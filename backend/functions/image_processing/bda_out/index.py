import json
import os
import re
import traceback
from urllib.parse import unquote_plus

import boto3
from db.mapping import Metrics, Message, MetricOrigin
from db.util import begin_session
from sqlalchemy import select, update, insert

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')

#  maybe pass blueprint attributes via env too todo


def process_output_file(bucket, key):
    s3_response = s3_client.get_object(Bucket=bucket, Key=key)
    file_content = s3_response['Body'].read().decode('utf-8')

    return [json.loads(line) for line in file_content.strip().split('\n') if line]


def handler(event, context):
    try:
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = unquote_plus(record['s3']['object']['key'])
        image_key_uuid_str = extract_uuid_from_key(object_key)


    except Exception as e:
        print(f"Error during key extraction/parsing: {e}")
        traceback.print_exc()
        return {'statusCode': 400, 'body': 'Invalid S3 key structure or missing UUID.'}

    image_descriptions = process_output_file(bucket_name, object_key)

    if not image_descriptions:
        print(f"No valid inference results found for key {image_key_uuid_str}.")
        return {'statusCode': 200, 'body': 'No data to write.'}

    session = begin_session()

    desc_data = image_descriptions[0].get('inference_result', {})

    image_description = desc_data.get('image_description')
    image_text = desc_data.get('image_text')
    try:

        message_query = select(Message).where(Message.image_key == image_key_uuid_str)
        target_message = session.scalar(message_query)
        message_id = target_message.id

        update_message_stmt = (
            update(Message.__table__)
            .where(Message.__table__.c.id == message_id)
            .values(
                image_description=image_description,
                image_text=image_text,
                image_described=True
            )
        )
        session.execute(update_message_stmt)
        print(f"Updated Message ID {image_key_uuid_str} with main description.")

        session.commit()

        send_text_to_sns(image_description, message_id, MetricOrigin.img_desc.value)
        send_text_to_sns(image_text, message_id, MetricOrigin.img_text.value)


    except Exception as e:
        session.rollback()
        print(f"Database transaction failed: {e}")
        traceback.print_exc()
        #  todo handle error
        return {'statusCode': 500, 'body': f"Couldn't process output due to the error: {traceback.format_exc()}."}

    finally:
        session.close()

    return {'statusCode': 200,
            'body': f"Processed output and potentially triggered tagging for Message ID {message_id}."}


def send_text_to_sns(image_description, message_id, origin):
    if image_description:
        sns_payload = {
            'message_id': message_id,
            'origin': origin
        }

        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(sns_payload),
            Subject='Media Processing Complete for Categorization'
        )

        print(f"Sent SNS message for final categorization of Message ID {message_id}.")


def extract_uuid_from_key(object_key: str) -> str:
    # Example input: 'a1b2c3d4-..../job-12345678/output.jsonl'

    parts = object_key.split('/')

    if parts and re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', parts[0], re.I):
        return parts[0]

    raise ValueError(f"Could not find a valid UUID in the expected prefix of the S3 key: {object_key}")

