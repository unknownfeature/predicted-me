import traceback

from backend.lib import constants
from backend.lib.db import setup_engine, Base


def handler(event, _):

    request_type = event[constants.request_type]

    if request_type == constants.create_request_type:
        print('Create event received. Initializing schema.')
        return on_create(event)


    return  {constants.resource_status: constants.resource_success}


def on_create(event):

    try:

        engine = setup_engine()

        print('Connecting to the database and creating schema...')
        Base.metadata.create_all(engine)
        print('Schema creation successful.')

        return  {constants.resource_status: constants.resource_success}

    except Exception as e:
        traceback.print_exc()
        return  {constants.resource_status: constants.resource_failed, constants.resource_reason: str(e)}