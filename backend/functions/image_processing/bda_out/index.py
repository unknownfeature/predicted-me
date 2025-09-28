import json
import os
import re
import traceback
import uuid
from urllib.parse import unquote_plus

import boto3
from sqlalchemy import create_engine, select, update, insert
from sqlalchemy.orm import sessionmaker
from lib.db import Metrics, Message

# {
#   "matched_blueprint": {
#     "arn": "arn:aws:bedrock:...",
#     "name": "ImageSummarizationBlueprint",
#     "confidence": 1.0
#   },
#   "inference_result": {
#     "main_description": "A detailed paragraph describing the image's main subject, scene, and composition.",
#     "detected_objects": [
#       "mountain bike",
#       "forest trail",
#       "helmet"
#     ],
#     "activities": [
#       "riding",
#       "mountain biking"
#     ],
#     "image_sentiment": "adventurous"
#   }
# }

s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')
sns_client = boto3.client('sns')

SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_ENDPOINT = os.environ.get('DB_ENDPOINT')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = 3306
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')



def extract_uuid_from_key(object_key: str) -> str:

    # Example input: 'a1b2c3d4-..../job-12345678/output.jsonl'

    parts = object_key.split('/')

    if parts and re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', parts[0], re.I):
        return parts[0]

    raise ValueError(f"Could not find a valid UUID in the expected prefix of the S3 key: {object_key}")


def begin_session():
    secret_response = secrets_client.get_secret_value(SecretId=SECRET_ARN)
    secret_dict = json.loads(secret_response['SecretString'])

    username = secret_dict['username']
    password = secret_dict['password']
    connection_string = (
        f'mysql+mysqlconnector://{username}:{password}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}'
    )

    engine = create_engine(connection_string, pool_recycle=300)

    return sessionmaker(bind=engine)()


def process_output_file(bucket, key):
    s3_response = s3_client.get_object(Bucket=bucket, Key=key)
    file_content = s3_response['Body'].read().decode('utf-8')

    return [json.loads(line) for line in file_content.strip().split('\n') if line ]


def handler(event, context):
    try:
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = unquote_plus(record['s3']['object']['key'])
        image_key_uuid_str = extract_uuid_from_key(object_key)
        image_key_uuid = uuid.UUID(image_key_uuid_str)


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

    try:
        message_query = select(Message).where(Message.image_key == image_key_uuid_str)
        target_message = session.scalar(message_query)
        message_id = target_message.id
        update_message_stmt = (
            update(Message.__table__)
            .where(Message.__table__.c.id == message_id)
            .values(
                image_text=desc_data.get('main_description'),
                image_described=True
            )
        )
        session.execute(update_message_stmt)
        print(f"Updated Message ID {image_key_uuid} with main description.")

        metrics_to_insert = []

        for item in desc_data.get('detected_objects', []) + desc_data.get('activities', []):
            metrics_to_insert.append({
                'message_id': message_id,
                'normalized_name': item,
                'original_name': item,
                'value': 1.0,
                'units': 'presence',
                'tagged': False
            })

        sentiment = desc_data.get('image_sentiment')
        if sentiment:
            metrics_to_insert.append({
                'message_id': message_id,
                'normalized_name': sentiment,
                'original_name': sentiment,
                'value': 1.0, # will be updated on extraction
                'units': 'magnitude',
                'tagged': True
            })

        if metrics_to_insert:
            insert_metrics_stmt = insert(Metrics.__table__).values(metrics_to_insert)
            session.execute(insert_metrics_stmt)
            print(f"Inserted {len(metrics_to_insert)} new metric rows.")

        session.commit()

        if desc_data.get('main_description'):
            sns_payload = {
                'message_id': message_id,
                'trigger_event': 'IMAGE_PROCESSED'
            }

            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps(sns_payload),
                Subject='Media Processing Complete for Categorization'
            )

            print(f"Sent SNS message for final categorization of Message ID {message_id}.")


    except Exception as e:
        session.rollback()
        print(f"Database transaction failed: {e}")
        traceback.print_exc()
        return {'statusCode': 500, 'body': f"Couldn't process output due to the error: {traceback.format_exc()}."}

    finally:
        session.close()

    return {'statusCode': 200,
            'body': f"Processed output and potentially triggered tagging for Message ID {message_id}."}