import traceback

from shared import constants
from backend.lib.db import setup_engine, Base


def handler(event, _):

    request_type = event[constants.request_type]

    if request_type == constants.create_request_type:
        print('Create event received. Initializing db.')
        return on_create()


    return  {constants.resource_status: constants.resource_success}


def on_create():

    try:

        engine = setup_engine(fix_auth=True)

        print('Connecting to the database and creating db...')
        Base.metadata.create_all(engine)
        print('Schema creation successful.')

        return  {constants.resource_status: constants.resource_success}

    except Exception as e:
        traceback.print_exc()
        return  {constants.resource_status: constants.resource_failed, constants.resource_reason: str(e)}