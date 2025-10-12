import unittest
import uuid
from unittest.mock import patch
import os

from backend.lib.db import begin_session, Note
from backend.tests.integration.base import baseTearDown, legit_user_id, baseSetUp
from shared.variables import Env

os.environ[Env.transcribe_bucket_out] = 'bucket_out'

from backend.lib import constants
from backend.functions.audio.transcribe_out.index import handler


class Test(unittest.TestCase):

    def setUp(self):
        baseSetUp(None)

    @patch('backend.functions.audio.transcribe_out.index.send_to_sns')
    @patch('backend.functions.audio.transcribe_out.index.read_job_result_json')
    def test_handler_succeeds(self, read_job_result_json_mock, send_to_sns_mock):
        key = uuid.uuid4().hex + '.mp4'
        self._setup_note(key)

        session = begin_session()
        try:
            note = session.query(Note).get(1)
            assert note.audio_key == key
            assert note.audio_text is None
            assert not note.audio_transcribed
        finally:
            session.close()

        text = 'the text'
        read_job_result_json_mock.return_value = {
            constants.job_name: key,
            constants.results: {
                constants.transcripts: [
                    {constants.transcript: text}
                ]
            }
        }

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
        read_job_result_json_mock.assert_called_once_with(key)
        send_to_sns_mock.assert_called_once_with(1)
        try:
            note = session.query(Note).get(1)
            assert note.audio_key == key
            assert note.audio_text == text
            assert note.audio_transcribed
        finally:
            session.close()

    @patch('backend.functions.audio.transcribe_out.index.send_to_sns')
    @patch('backend.functions.audio.transcribe_out.index.read_job_result_json')
    def test_handler_failes_on_invalid_event(self, read_job_result_json_mock, send_to_sns_mock):
        event = {}
        res = handler(event, None)
        assert res[constants.status] == constants.error
        assert res[constants.error] is not None
        send_to_sns_mock.assert_not_called()
        read_job_result_json_mock.assert_not_called()

    @patch('backend.functions.audio.transcribe_out.index.send_to_sns')
    @patch('backend.functions.audio.transcribe_out.index.read_job_result_json')
    def test_handler_failes_on_invalid_key(self, read_job_result_json_mock, send_to_sns_mock):
        key = uuid.uuid4().hex + '.mp4'
        self._setup_note(key)
        other_key = 'some_other_key'

        session = begin_session()
        try:
            note = session.query(Note).get(1)
            assert note.audio_key == key
            assert note.audio_text is None
            assert not note.audio_transcribed
        finally:
            session.close()

        text = 'the text'
        read_job_result_json_mock.return_value = {
            constants.job_name: other_key,
            constants.results: {
                constants.transcripts: [
                    {constants.transcript: text}
                ]
            }
        }

        event = {
            constants.records: [{
                constants.s3: {
                    constants.object: {
                        constamts.s3_key: other_key
                    }
                }
            }]
        }
        res = handler(event, None)
        assert res[constants.status] == constants.error
        assert res[constants.error] is not None
        read_job_result_json_mock.assert_called_once_with(other_key)
        send_to_sns_mock.assert_not_called()

    @patch('backend.functions.audio.transcribe_out.index.send_to_sns')
    @patch('backend.functions.audio.transcribe_out.index.read_job_result_json')
    def test_handler_fails_for_non_existing_note(self, read_job_result_json_mock, send_to_sns_mock):
        key = uuid.uuid4().hex + '.mp4'


        session = begin_session()
        try:
            note = session.query(Note).get(1)
            assert note is None

        finally:
            session.close()

        text = 'the text'
        read_job_result_json_mock.return_value = {
            constants.job_name: key,
            constants.results: {
                constants.transcripts: [
                    {constants.transcript: text}
                ]
            }
        }

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
        assert res[constants.status] == constants.error
        assert res[constants.error] is not None
        read_job_result_json_mock.assert_called_once_with(key)
        send_to_sns_mock.assert_not_called()


    def _setup_note(self, audio_key: str):
        session = begin_session()
        try:
            session.add(Note(user_id=legit_user_id, audio_key=audio_key))
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
