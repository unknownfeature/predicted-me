import unittest
import uuid
from unittest.mock import patch, call

from backend.functions.audio.transcribe_out.index import handler
from backend.functions.image.bda_out.index import handler
from backend.lib import constants
from backend.lib.db import begin_session, Note, Origin
from backend.tests.integration.base import baseTearDown, legit_user_id, baseSetUp

class Test(unittest.TestCase):

    def setUp(self):
        baseSetUp(None)

    @patch('backend.functions.image.bda_out.index.send_text_to_sns')
    @patch('backend.functions.image.bda_out.index.read_data_from_output_file')
    def test_handler_succeeds(self, read_data_from_output_file_mock, send_text_to_sns_mock):
        key = uuid.uuid4().hex + '.img'
        self._setup_note(key)

        session = begin_session()
        try:
            note = session.query(Note).get(1)
            assert note.image_key == key
            assert note.image_text is None
            assert note.image_description is None
            assert not note.image_described
        finally:
            session.close()

        image_text = 'image text'
        image_description = 'image description'
        read_data_from_output_file_mock.return_value = [{
            constants.inference_result: {
               constants.image_description: image_description,
               constants.image_text: image_text
            }
        }]

        whatever = 'whatever'
        event = {
            constants.records: [{
                constants.s3: {
                    constants.object: {
                        constants.key: key
                    },
                    constants.bucket: {
                        constants.name: whatever
                    }
                }
            }]
        }
        res = handler(event, None)
        assert res[constants.status] == constants.success

        read_data_from_output_file_mock.assert_called_once_with(whatever, key)


        send_text_to_sns_mock.assert_has_calls([call(image_description, 1, Origin.img_desc.value), call(image_text, 1, Origin.img_text.value)])

        try:
            note = session.query(Note).get(1)
            assert note.image_key == key
            assert note.image_text == image_text
            assert note.image_description == image_description
            assert note.image_described
        finally:
            session.close()

    @patch('backend.functions.image.bda_out.index.send_text_to_sns')
    @patch('backend.functions.image.bda_out.index.read_data_from_output_file')
    def test_handler_failes_on_invalid_event(self, read_data_from_output_file_mock, send_text_to_sns_mock):
        event = {}
        res = handler(event, None)
        assert res[constants.status] == constants.error
        send_text_to_sns_mock.assert_not_called()
        read_data_from_output_file_mock.assert_not_called()

    @patch('backend.functions.image.bda_out.index.send_text_to_sns')
    @patch('backend.functions.image.bda_out.index.read_data_from_output_file')
    def test_handler_failes_on_invalid_key(self, read_data_from_output_file_mock, send_text_to_sns_mock):
        key = uuid.uuid4().hex + '.img'
        self._setup_note(key)
        other_key = 'some_other_key'

        session = begin_session()
        try:
            note = session.query(Note).get(1)
            assert note.image_key == key
            assert note.image_text is None
            assert note.image_description is None
            assert not note.image_described
        finally:
            session.close()


        image_text = 'image text'
        image_description = 'image description'
        read_data_from_output_file_mock.return_value = [{
            constants.inference_result: {
               constants.image_description: image_description,
               constants.image_text: image_text
            }
        }]

        whatever = 'whatever'
        event = {
            constants.records: [{
                constants.s3: {
                    constants.object: {
                        constants.key: other_key
                    },
                    constants.bucket: {
                        constants.name: whatever
                    }
                }
            }]
        }
        res = handler(event, None)
        assert res[constants.status] == constants.error
        read_data_from_output_file_mock.assert_called_once_with(whatever, other_key)
        send_text_to_sns_mock.assert_not_called()

    @patch('backend.functions.image.bda_out.index.send_text_to_sns')
    @patch('backend.functions.image.bda_out.index.read_data_from_output_file')
    def test_handler_fails_for_non_existing_note(self, read_data_from_output_file_mock, send_text_to_sns_mock):
        key = uuid.uuid4().hex + '.img'


        session = begin_session()
        try:
            note = session.query(Note).get(1)
            assert note is None

        finally:
            session.close()

        image_text = 'image text'
        image_description = 'image description'
        read_data_from_output_file_mock.return_value = [{
            constants.inference_result: {
               constants.image_description: image_description,
               constants.image_text: image_text
            }
        }]

        whatever = 'whatever'
        event = {
            constants.records: [{
                constants.s3: {
                    constants.object: {
                        constants.key: key
                    },
                    constants.bucket: {
                        constants.name: whatever
                    }
                }
            }]
        }
        res = handler(event, None)
        assert res[constants.status] == constants.error
        read_data_from_output_file_mock.assert_called_once_with(whatever, key)
        send_text_to_sns_mock.assert_not_called()


    def _setup_note(self, img_key: str):
        session = begin_session()
        try:
            session.add(Note(user_id=legit_user_id, image_key=img_key))
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
