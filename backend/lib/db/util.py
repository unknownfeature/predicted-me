import json
import os

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_ENDPOINT = os.environ.get('DB_ENDPOINT')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = 3306

secrets_client = boto3.client('secretsmanager')

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