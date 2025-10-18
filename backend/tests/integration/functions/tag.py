import json
import unittest
from backend.tests.integration.base import *
from backend.functions.tag.index import handler
from backend.lib.util import get_user_ids_from_event


tag_one_display_name = 'display name one'
tag_two_display_name = 'display name two'
tag_three_display_name = 'display name  three' + unique_piece
tag_four_display_name = 'display name our'
tag_five_display_name = 'display name five'


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_post_returns_500(self):

        self.event[constants.body] = {
        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])[constants.error] == constants.internal_server_error
        session = begin_session()

        try:
            assert len(get_tags_by_display_name(tag_one_display_name, session)) == 0
        finally:
            session.close()

    def test_tag_post_fails_for_duplicate(self):

        self._setup_tags()
        session = begin_session()

        try:

            self.event[constants.body] = {
                constants.name: tag_two_name,
            }
            self.event[constants.http_method] = constants.post
            result = handler(self.event, None)

            assert result[constants.status_code] == 500


        finally:
            session.close()

    #  todo finish this
    def test_tag_post_succeeds_for_duplicate_from_another_user(self):

         self._setup_tags()
         session = begin_session()

         try:
             malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
             malicious_event[constants.body] = {
                 constants.name: tag_two_display_name,
             }
             malicious_event[constants.http_method] = constants.post
             result = handler(malicious_event, None)

             assert result[constants.status_code] == 201

         finally:
             session.close()

    def test_tag_post_succeeds(self):

        self.event[constants.body] = {
            constants.name: tag_one_display_name,
        }

        self.event[constants.http_method] = constants.post

        result = handler(self.event, None)
        assert result[constants.status_code] == 201
        assert json.loads(result[constants.body])[constants.id] is not None

        session = begin_session()

        try:

            tags = get_tags_by_display_name(tag_one_display_name, session)
            assert len(tags) == 1

            user = tags[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure user is correct
            assert user_id == user.user_id
            assert user.user.external_id == external_id


        finally:
            session.close()



    def test_tag_get_by_display_name_succeeds(self):

        self._setup_tags()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.name: 'one',

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            prev_tag_id = items[0][constants.id]

            self.event[constants.query_params] = {
                constants.name: unique_piece,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1  # in display_name
            this_tag_id = items[0][constants.id]

            assert prev_tag_id != this_tag_id

            ###############################################
            # pagination
            ##############################################

            # offset defaults to 0 and limit to 100 so all 5 return
            self.event[constants.query_params] = {

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 5

            # offset defaults to 0, limit 4 so 4 return
            self.event[constants.query_params] = {
                constants.limit: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 4

            # offset defaults 4, limit 100 abd we only have 5 left so 1 will return
            self.event[constants.query_params] = {
                constants.offset: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 1

        finally:
            session.close()

    def test_tag_get_by_display_name_fails_for_malicious_user(self):
        self._setup_tags()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.name: 'one',
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0


        finally:
            session.close()

    def _setup_tags(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(user_id=user_id, name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(user_id=user_id, name=tag_two_name, display_name=tag_two_display_name)

            tag_three = Tag(user_id=user_id, name=tag_three_name, display_name=tag_three_display_name)

            tag_four = Tag(user_id=user_id, name=normalize_identifier(tag_four_display_name), display_name=tag_four_display_name)

            tag_five = Tag(user_id=user_id, name=normalize_identifier(tag_five_display_name), display_name=tag_five_display_name)

            session.add_all([tag_one, tag_two, tag_three, tag_four, tag_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
