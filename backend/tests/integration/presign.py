import unittest
import uuid
from unittest.mock import patch
import os
from shared.variables import Env
os.environ[Env.bda_input_bucket_name] = 'image'
os.environ[Env.transcribe_bucket_in] = 'audio'
from backend.tests.integration.base import baseSetUp, baseTearDown, Trigger

from backend.lib import constants
from backend.functions.presign.index import handler, get_extension

# todo fix tests
class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    @patch('backend.functions.presign.index.generate_presigned_url')
    @patch('backend.functions.presign.index.generate_key')
    def test_handler_succeeds_for_audio_put(self, generate_key_mock, generate_presigned_url_mock):
        ps_url =  'https://presigned.url'
        key = uuid.uuid4().hex
        generate_presigned_url_mock.return_value = ps_url
        generate_key_mock.return_value = key

        event = self.event
        event[constants.http_method] = constants.get
        event[constants.query_params] = {
            constants.extension: 'mp4',
            constants.method: constants.put
        }
        res = handler(event, None)
        assert res[constants.status_code] == 200
        generate_key_mock.assert_called()
        generate_presigned_url_mock.assert_called_once_with('audio',  'audio/mp4', key + '.mp4', 'put_object')

    @patch('backend.functions.presign.index.generate_presigned_url')
    @patch('backend.functions.presign.index.generate_key')
    def test_handler_succeeds_for_image_put(self, generate_key_mock, generate_presigned_url_mock):
        ps_url = 'https://presigned.url'
        key = uuid.uuid4().hex
        generate_presigned_url_mock.return_value = ps_url
        generate_key_mock.return_value = key

        event = self.event
        event[constants.http_method] = constants.get
        event[constants.query_params] = {
            constants.extension: 'jpg',
            constants.method: constants.put
        }
        res = handler(event, None)
        assert res[constants.status_code] == 200
        generate_key_mock.assert_called()
        generate_presigned_url_mock.assert_called_once_with('image', 'image/jpeg', key + '.jpg', 'put_object')

    @patch('backend.functions.presign.index.generate_presigned_url')
    @patch('backend.functions.presign.index.generate_key')
    def test_handler_succeeds_for_audio_get(self, generate_key_mock, generate_presigned_url_mock):
        ps_url = 'https://presigned.url'
        key = uuid.uuid4().hex
        generate_presigned_url_mock.return_value = ps_url
        generate_key_mock.return_value = key

        event = self.event
        event[constants.http_method] = constants.get
        event[constants.query_params] = {
            constants.extension: 'mp4',
            constants.method: constants.get
        }
        res = handler(event, None)
        assert res[constants.status_code] == 200
        generate_key_mock.assert_called()
        generate_presigned_url_mock.assert_called_once_with('audio', 'audio/mp4',  key + '.mp4', 'get_object')

    @patch('backend.functions.presign.index.generate_presigned_url')
    @patch('backend.functions.presign.index.generate_key')
    def test_handler_succeeds_for_image_get(self, generate_key_mock, generate_presigned_url_mock):
        ps_url = 'https://presigned.url'
        key = uuid.uuid4().hex
        generate_presigned_url_mock.return_value = ps_url
        generate_key_mock.return_value = key

        event = self.event
        event[constants.http_method] = constants.get
        event[constants.query_params] = {
            constants.extension: 'jpg',
            constants.method: constants.get
        }
        res = handler(event, None)
        assert res[constants.status_code] == 200
        generate_key_mock.assert_called()
        generate_presigned_url_mock.assert_called_once_with('image', 'image/jpeg',  key + '.jpg', 'get_object')

    @patch('backend.functions.presign.index.generate_presigned_url')
    def test_handler_returns_error_on_invalid_event(self, generate_presigned_url_mock):
        event = {}
        event[constants.http_method] = constants.get
        res = handler(event, None)
        assert res[constants.status_code] == 500
        assert res[constants.body] is not None
        generate_presigned_url_mock.assert_not_called()

    def test_handler_returns_error_on_not_suppoerted_method(self,):

        event = self.event
        event[constants.http_method] = constants.post
        event[constants.query_params] = {
            constants.extension: 'mp4',
            constants.method: constants.get
        }
        res = handler(event, None)
        assert res[constants.status_code] == 405

    def test_extension_extracted(self,):

        assert get_extension('hello.x') == 'x'

    def tearDown(self):
        baseTearDown()