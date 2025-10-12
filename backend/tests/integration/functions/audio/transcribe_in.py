import unittest
import uuid
from unittest.mock import patch
import os
from shared.variables import Env
os.environ[Env.transcribe_bucket_in] = 'bucket_in'
os.environ[Env.transcribe_bucket_out] = 'bucket_out'

from backend.lib import constants
from backend.functions.audio.transcribe_in.index import handler


class Test(unittest.TestCase):

    @patch('backend.functions.audio.transcribe_in.index.start_transcription_job')
    def test_handler_succeeds(self, start_transcription_job_mock):
        key = uuid.uuid4().hex + '.mp4'
        event = {
            constants.records: [{
                constants.s3: {
                    constants.object: {
                        constamts.s3_key: key
                    }
                }
            }]
        }
        res = handler(event, None)
        assert res[constants.status] == constants.success
        start_transcription_job_mock.assert_called_once_with(f"s3://bucket_in/{key}", key, 'MP4')


    @patch('backend.functions.audio.transcribe_in.index.start_transcription_job')
    def test_handler_returns_error_on_invalid_event(self, start_transcription_job_mock):
        event = {}
        res = handler(event, None)
        assert res[constants.status] == constants.error
        assert res[constants.error] is not None
        start_transcription_job_mock.assert_not_called()