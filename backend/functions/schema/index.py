import traceback

import boto3

from backend.lib.db import setup_engine, Base

secrets_client = boto3.client(constants.secretsmanager)


def handler(event, _):

    request_type = event[constants.RequestType]

    if request_type == constants.Create:
        print("Create event received. Initializing schema.")
        return on_create(event)


    return {constants.status: constants.success}


def on_create(event):


    try:

        engine = setup_engine()

        print("Connecting to the database and creating schema...")
        Base.metadata.create_all(engine)
        print("Schema creation successful.")

        return {constants.status: constants.success}

    except Exception as e:
        traceback.print_exc()
        return {constants.Status: constants.FAILED, constants.Reason: str(e)}