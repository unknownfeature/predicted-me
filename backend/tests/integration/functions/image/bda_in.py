import unittest
import uuid
from unittest.mock import patch
import os
from shared.variables import *

os.environ[bda_output_bucket_name] = 'bda_bucket'
os.environ[bda_job_execution_role_arn] = 'role'
os.environ[bda_blueprint_name] = 'blueprint'
os.environ[bda_model_name] = 'model'

from shared import constants
from backend.functions.image.bda_in.index import handler


class Test(unittest.TestCase):

    @patch('backend.functions.image.bda_in.index.start_bda_job')
    def test_handler_succeeds(self, start_bda_job_mock):

        key = uuid.uuid4().hex + '.img'
        in_bucket = 'in_bucket'
        event = {
            constants.records: [{
                constants.s3: {
                    constants.object: {
                        constants.s3_key: key
                    },
                    constants.bucket: {
                        constants.name: in_bucket
                    }
                }
            }]
        }
        res = handler(event, None)
        assert res[constants.status] == constants.success
        input_s3_uri = f's3://{in_bucket}/{key}'
        output_s3_uri = f's3://bda_bucket/{key}/'
        start_bda_job_mock.assert_called_once_with(key, input_s3_uri, output_s3_uri)


    @patch('backend.functions.image.bda_in.index.start_bda_job')
    def test_handler_returns_error_on_invalid_event(self, start_bda_job_mock):
        event = {}
        res = handler(event, None)
        assert res[constants.status] == constants.error
        assert res[constants.error] is not None
        start_bda_job_mock.assert_not_called()