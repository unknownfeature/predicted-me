import json
import os

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared import Env

secret_arn = os.getenv(Env.db_secret_arn)
db_endpoint = os.getenv(Env.db_endpoint)
db_name = os.getenv(Env.db_name)
db_port = 3306

secrets_client = boto3.client('secretsmanager')


def begin_session():
    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    secret_dict = json.loads(secret_response['SecretString'])

    username = secret_dict['username']
    password = secret_dict['password']
    connection_string = (
        f'mysql+mysqlconnector://{username}:{password}@{db_endpoint}:{db_port}/{db_name}'
    )

    engine = create_engine(connection_string, pool_recycle=300)

    return sessionmaker(bind=engine)()
