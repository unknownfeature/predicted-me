import json
import os
import traceback
from urllib.parse import unquote_plus

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_ENDPOINT = os.environ.get('DB_ENDPOINT')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = 3306



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
    except Exception as e:
        print(f"Error extracting S3 details: {e}")
        return {'statusCode': 400, 'body': 'Invalid S3 event format.'}

    image_descriptions = process_output_file(bucket_name, object_key)

    if not image_descriptions:
        print("No valid inference results found.")
        return {'statusCode': 200, 'body': 'No data to write.'}


    session = begin_session()

    try:
        for desc_data in image_descriptions:
            # todo write actual insertion logic after schema is defined
            session.execute(insert_stmt)

        session.commit()
        print(f"Successfully wrote {len(image_descriptions)} records to database.")

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return {'statusCode': 500, 'body': f"Couldn't process output due to the error {traceback.format_exc()}."}

    finally:
        session.close()

    return {'statusCode': 200, 'body': f"Processed {len(image_descriptions)} descriptions."}