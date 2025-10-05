import traceback

import boto3

from backend.lib.db import setup_engine, Base

secrets_client = boto3.client('secretsmanager')


def handler(event, _):

    request_type = event['RequestType']

    if request_type == 'Create':
        print("Create event received. Initializing schema.")
        return on_create(event)


    return {'status': 'success'}


def on_create(event):


    try:

        engine = setup_engine()

        print("Connecting to the database and creating schema...")
        Base.metadata.create_all(engine)
        print("Schema creation successful.")

        return {'status': 'success'}

    except Exception as e:
        traceback.print_exc()
        return {'Status': 'FAILED', 'Reason': str(e)}