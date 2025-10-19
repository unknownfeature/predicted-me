import json
import unittest

from backend.tests.integration.base import *
from backend.functions.user.index import handler


class Test(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_user_post_succeeds(self):
        new_external_id = uuid.uuid4().hex
        event = prepare_http_event(new_external_id)

        event[constants.body] = json.dumps({
            constants.name: 'Test User',
            constants.links_enabled: True,
            constants.tasks_enabled: False
        })

        event[constants.request_context] = event[constants.request_context] | {
            constants.http: {constants.method: constants.post}}
        result = handler(event, None)
        assert result[constants.status_code] == 201
        id = json.loads(result[constants.body])[constants.id]
        assert id is not None

        session = begin_session()
        try:
            created_user = get_user_by_id(id, session)
            assert created_user.external_id == new_external_id
            assert created_user.name == 'Test User'
            assert created_user.links_enabled is True
            assert created_user.tasks_enabled is False
        finally:
            session.close()

    def test_get_user_succeeds(self):
        session = begin_session()
        try:
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}
            result = handler(self.event, None)
            assert result[constants.status_code] == 200

            user = json.loads(result[constants.body])

            assert user[constants.id] == legit_user_id
            assert user[constants.name] is None
            assert user[constants.links_enabled] is False
            assert user[constants.tasks_enabled] is False
        finally:
            session.close()

    def test_get_user_succeeds_malicious_user_for_its_own_user(self):
        session = begin_session()
        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}

            result = handler(malicious_event, None)
            user = json.loads(result[constants.body])

            assert user[constants.id] == malicious_user_id
            assert user[constants.name] is None
            assert user[constants.links_enabled] is False
            assert user[constants.tasks_enabled] is False
        finally:
            session.close()

    def test_user_patch_succeeds(self):
        session = begin_session()
        try:
            user_before = get_user_by_id(legit_user_id, session)
            assert user_before.name is None
            assert user_before.links_enabled is False
            assert user_before.tasks_enabled is False

            self.event[constants.body] = json.dumps({
                constants.name: 'New Name',
                constants.links_enabled: True
            })
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.patch}}

            result = handler(self.event, None)
            assert result[constants.status_code] == 204

            session = refresh_cache(session)
            user_after = get_user_by_id(legit_user_id, session)
            assert user_after.name == 'New Name'
            assert user_after.links_enabled is True
            assert user_after.tasks_enabled is False
        finally:
            session.close()

    def test_user_patch_fails_for_malicious_user_on_other_user(self):
        session = begin_session()
        try:

            user_before = get_user_by_id(legit_user_id, session)
            assert user_before.name is None

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = json.dumps({
                constants.name: 'Hacked Name'
            })
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.patch}}

            result = handler(malicious_event, None)
            assert result[constants.status_code] == 204

            session = refresh_cache(session)
            user_after = get_user_by_id(legit_user_id, session)
            assert user_after.name is None

            malicious_user_after = get_user_by_id(malicious_user_id, session)
            assert malicious_user_after.name == 'Hacked Name'
        finally:
            session.close()

    def test_user_delete_succeeds(self):
        session = begin_session()
        try:
            user_before = get_user_by_id(legit_user_id, session)
            assert user_before is not None

            self.event[constants.body] = json.dumps({})
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.delete}}

            result = handler(self.event, None)
            assert result[constants.status_code] == 204

            session = refresh_cache(session)
            user_after = get_user_by_id(legit_user_id, session)
            assert user_after is None
        finally:
            session.close()

    def test_user_delete_succeeds_for_malicious_user_on_own_account(self):
        session = begin_session()
        try:
            legit_user_before = get_user_by_id(legit_user_id, session)
            assert legit_user_before is not None

            malicious_user_before = get_user_by_id(malicious_user_id, session)
            assert malicious_user_before is not None

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = json.dumps({})
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.delete}}

            result = handler(malicious_event, None)
            assert result[constants.status_code] == 204

            session = refresh_cache(session)

            legit_user_after = get_user_by_id(legit_user_id, session)
            assert legit_user_after is not None

            malicious_user_after = get_user_by_id(malicious_user_id, session)
            assert malicious_user_after is None
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()