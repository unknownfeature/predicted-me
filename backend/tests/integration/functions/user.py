import json
import unittest

from backend.tests.integration.base import *

from backend.functions.user.index import handler


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)


    def test_tag_post_succeeds(self):

        new_external_id = uuid.uuid4().hex
        event = prepare_http_event(new_external_id)
        event[constants.http_method] = constants.post
        result = handler(event, None)
        assert result[constants.status_code] == 201
        id = json.loads(result[constants.body])[constants.id]
        assert id is not None

        session = begin_session()

        try:

            created_user = get_user_by_id(id, session)
            assert created_user.external_id == new_external_id

        finally:
            session.close()



    def test_get_user_succeeds(self):


        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            user = json.loads(result[constants.body])
            assert user[constants.id] == legit_user_id

        finally:
            session.close()

    def test_get_user_succeeds_malicious_user_for_its_own_user(self):

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            result = handler(malicious_event, None)
            user = json.loads(result[constants.body])
            assert user[constants.id] == malicious_user_id


        finally:
            session.close()


    def tearDown(self):
        baseTearDown()
