import json
import unittest

from backend.functions.link.index import handler
from backend.lib.db import Tag, Note, Link, Origin
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *

link_one_url = 'http://one'
link_two_url = 'http://two'
link_three_url = 'http://three/' + unique_piece
link_four_url = 'http://four'
link_five_url = 'http://five'

link_one_description = 'description for link one'
link_two_description = 'description for link two'
link_three_description = 'description for link three'
link_four_description = 'description for link four'
link_five_description = 'description for link five ' + unique_piece


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)


    def test_links_get_by_date_succeeds(self):
        session = begin_session()
        try:
            self._setup_links_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: three_days_ago,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0



            #############################################

            self.event[constants.query_params] = {}  # should default to now - 1d

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1

            assert items[0][constants.url] == link_four_url
            assert items[0][constants.description] == link_four_description


            #############################################
            self.event[constants.query_params] = {
                constants.start: two_days_ago,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.url] == link_four_url
            assert items[0][constants.description] == link_four_description

            assert items[1][constants.url] == link_three_url
            assert items[1][constants.description] == link_three_description
            ##############################################
            self.event[constants.query_params] = {
                constants.end: two_days_ago,
            }
            result = handler(self.event, None)
            items = json.loads(result[constants.body])
            assert len(items) == 3
            assert items[0][constants.url] == link_one_url
            assert items[1][constants.url] == link_five_url
            assert items[2][constants.url] == link_two_url

            assert items[0][constants.description] == link_one_description
            assert items[1][constants.description] == link_five_description
            assert items[2][constants.description] == link_two_description

            assert session.query(Link).count() == 5

        finally:
            session.close()

    def test_links_get_by_date_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_links_for_search(session)

            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(), #
            }
            malicious_event[constants.path_params] = {}
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user
        finally:
            session.close()

    def _setup_links_for_search(self, session):
        user_id, external_user_id = get_user_ids_from_event(self.event, session)

        tag_one = Tag(name=tag_one_name, display_name=tag_one_display_name)
        tag_two = Tag(name=tag_two_name, display_name=tag_two_display_name)

        tag_three = Tag(name=tag_three_name, display_name=tag_three_display_name)

        user = session.query(User).get(user_id)

        assert user.external_id == external_user_id
        note = Note(user=user)
        session.add(note)
        session.flush()
        # 3d| l2  l1  l5 | 2d| l3 | 1d |  l4 |now
        link_one = Link(note=note, user=user, url=link_one_url, description=link_one_description,
                        tags=[tag_one, tag_two], time=two_days_ago - 60, origin=Origin.audio_text)
        link_two = Link(user=user, url=link_two_url, description=link_two_description, tags=[tag_one, tag_three], time=three_days_ago + 60, origin=Origin.user)
        link_three = Link(note=note, user=user, url=link_three_url, description=link_three_description,
                          tags=[tag_three, tag_two], time=day_ago - 60, origin=Origin.audio_text )
        link_five = Link(user=user, url=link_five_url, description=link_five_description,
                         tags=[tag_one, tag_two], time=two_days_ago - 60, origin=Origin.user )
        link_four = Link(note=note, user=user, url=link_four_url, description=link_four_description,
                         tags=[tag_two, tag_three], time= get_utc_timestamp() - 60, origin=Origin.audio_text)
        session.add_all([note, link_one, link_two, link_three, link_four, link_five])
        session.commit()

    def tearDown(self):
        baseTearDown()
