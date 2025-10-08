import json
import unittest

from backend.functions.link.index import handler
from backend.lib.db import Tag, Note, Origin
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

    def test_incomplete_post_returns_500(self):


        self.event[constants.body] = {
            constants.description: link_one_description,

        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])['error'] == constants.internal_server_error
        session = begin_session()

        try:
            assert len(get_links_by_description(link_one_description, session)) == 0
        finally:
            session.close()

    def test_link_post_fails_for_duplicate(self):

        self._setup_links()
        session = begin_session()

        try:

            self.event[constants.body] = {
                constants.url: link_two_url,
                constants.description: link_two_description + unique_piece,
            }
            self.event[constants.http_method] = constants.post
            result = handler( self.event, None)

            assert result[constants.status_code] == 500


        finally:
            session.close()


    def test_link_post_succeeds_for_duplicate_from_another_user(self):

         self._setup_links()
         session = begin_session()

         try:
             malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
             malicious_event[constants.body] = {
                 constants.url: link_one_url,
                 constants.description: link_one_description,
             }
             malicious_event[constants.http_method] = constants.post
             result = handler(malicious_event, None)

             assert result[constants.status_code] == 201

         finally:
             session.close()

    def test_link_post_succeeds(self):

        self.event[constants.body] = {
            constants.url: link_one_url,
            constants.description: link_one_description,
        }

        self.event[constants.http_method] = constants.post

        result = handler(self.event, None)
        assert result[constants.status_code] == 201
        assert json.loads(result[constants.body])[constants.id] is not None

        session = begin_session()

        try:

            links = get_links_by_description(link_one_description, session)
            assert len(links) == 1

            user = links[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure user is correct
            assert user_id == user.user_id
            assert user.user.external_id == external_id


        finally:
            session.close()

    def test_link_patch_succeeds(self):
        self._setup_links()

        session = begin_session()

        try:

            links = get_links_by_description(link_one_description, session)

            assert len(links) == 1
            link = links[0]

            assert link.url == link_one_url
            assert len(link.tags) == 2

            old_tag_names = [tag.display_name for tag in link.tags]
            assert tag_one_display_name in old_tag_names
            assert tag_two_display_name in old_tag_names
            link_id = link.id

            new_time = 25
            new_tag_name = 'new_tag'
            self.event[constants.body] = {
                constants.url: link_two_url + unique_piece,
                constants.description: link_two_description,
                constants.time: new_time,
                #  one exists and one new, both should replace old ones
                constants.tags: [new_tag_name, tag_three_display_name]
            }
            self.event[constants.path_params][constants.id] = link_id
            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            link = get_link_by_id(link_id, session)

            # but with updated fields
            assert link.url == link_two_url + unique_piece
            assert link.description == link_two_description
            assert link.time == link.time # time is not updatable
            assert len(link.tags) == 2

            new_tag_names = [tag.display_name for tag in link.tags]
            assert new_tag_name in new_tag_names
            assert tag_three_display_name in new_tag_names

            #  make sure new tag was added and old tags were
            assert session.query(Tag).count() == 4

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()

    def test_link_patch_fails_for_malicious_user(self):

        self._setup_links()
        session = begin_session()

        try:

            links = get_links_by_description(link_one_description, session)

            assert len(links) == 1
            link = links[0]

            assert link.url == link_one_url

            link_id = link.id
            old_time = link.time

            new_time = 25
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {
                constants.url: link_two_url,
                constants.description: link_two_description,
                constants.time: new_time,
            }
            malicious_event[constants.path_params][constants.id] = link_id
            malicious_event[constants.http_method] = constants.patch
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            link = get_link_by_id(link_id, session)

            # but with updated fields
            assert link.url == link_one_url
            assert link.description == link_one_description
            assert link.time == old_time

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()

    def test_link_delete_succeeds(self):
        self._setup_links()
        session = begin_session()

        try:
            links = get_links_by_description(link_two_description, session)

            assert len(links) == 1
            link = links[0]
            link_id = link.id

            self.event = prepare_http_event(get_user_by_id(legit_user_id, session).external_id)
            self.event[constants.body] = {}
            self.event[constants.path_params][constants.id] = link_id
            self.event[constants.http_method] = constants.delete
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache
            session = refresh_cache(session)

            # make sure it didn't insert ore links
            links = get_links_by_description(link_two_description, session)
            assert len(links) == 0

        finally:
            session.close()

    def test_link_delete_fails_for_malicious_user(self):

        self._setup_links()
        session = begin_session()

        try:
            links = get_links_by_description(link_two_description, session)

            assert len(links) == 1
            link = links[0]
            link_id = link.id

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {}
            malicious_event[constants.path_params][constants.id] = link_id
            malicious_event[constants.http_method] = constants.delete
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            # new cache
            session = refresh_cache(session)

            links = get_links_by_description(link_two_description, session)
            assert len(links) == 1

        finally:
            session.close()

    def test_link_get_by_link_id_succeeds(self):

        self._setup_links()

        session = begin_session()
        try:
            self.event[constants.http_method] = constants.get

            self.event[constants.path_params][constants.id] = 1
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            assert items[0][constants.id] == 1

            self.event[constants.query_params] = {}
            self.event[constants.path_params] = {}
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1

        finally:
            session.close()

    def test_link_get_by_link_id_fails_for_malicious_user(self):

        self._setup_links()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}

            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()

    def test_link_get_by_note_succeeds(self):
        self._setup_links()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get

            self.event[constants.query_params] = {
                constants.note_id: 1,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3
            assert items[0][constants.note_id] == 1
            assert items[0][constants.origin] == Origin.audio_text.value

            self.event[constants.query_params] = {
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1


        finally:
            session.close()

    def test_link_get_by_note_fails_for_malicious_user(self):

        self._setup_links()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            malicious_event[constants.query_params] = {
                constants.note_id: 1,
                # start and end will be  == now - 1 day which is outside for this particular data point but it should be ignored
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()

    def test_link_get_by_tags_display_names_succeeds(self):

        self._setup_links()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 4

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5

        finally:
            session.close()

    def test_link_get_by_tags_display_names_fails_for_malicious_user(self):

        self._setup_links()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp()
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()

    def test_link_get_by_url_and_description_succeeds(self):

        self._setup_links()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.link: 'one',
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            prev_link_id = items[0][constants.id]

            self.event[constants.query_params] = {
                constants.link: unique_piece,
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2 # in url and description
            this_link_id = items[0][constants.id]

            assert prev_link_id != this_link_id

        finally:
            session.close()

    def test_link_get_by_description_fails_for_malicious_user(self):
        self._setup_links()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.link: link_one_description,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0


        finally:
            session.close()

    def test_links_get_by_date_succeeds(self):
        self._setup_links()
        session = begin_session()
        try:
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

            assert items[0][constants.tagged]
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

            ###############################################
            # pagination
            ##############################################

            # offset defaults to 0 and limit to 100 so all 5 return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 5

            # offset defaults to 0, limit 4 so 4 return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
                constants.limit: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 4

            # offset defaults 4, limit 100 abd we only have 5 left so 1 will return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
                constants.offset: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 1

            assert session.query(Link).count() == 5

        finally:
            session.close()

    def test_links_get_by_date_fails_for_malicious_user(self):

        self._setup_links()
        session = begin_session()
        try:

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

    def _setup_links(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(user_id=user_id, name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(user_id=user_id, name=tag_two_name, display_name=tag_two_display_name)

            tag_three = Tag(user_id=user_id, name=tag_three_name, display_name=tag_three_display_name)

            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            link_one = Link(note=note, user=user, url=link_one_url, description=link_one_description, tagged = True,
                            tags=[tag_one, tag_two], time=two_days_ago - 60, origin=Origin.audio_text)
            link_two = Link(user=user, url=link_two_url, description=link_two_description, tagged = True,
                            tags=[tag_one, tag_three], time=three_days_ago + 60, origin=Origin.user)
            link_three = Link(note=note, user=user, url=link_three_url, description=link_three_description, tagged = True,
                              tags=[tag_three, tag_two], time=day_ago - 60, origin=Origin.audio_text )
            link_four = Link(note=note, user=user, url=link_four_url, description=link_four_description, tagged = True,
                             tags=[tag_two, tag_three], time= get_utc_timestamp() - 60, origin=Origin.audio_text)
            link_five = Link(user=user, url=link_five_url, description=link_five_description, tagged = True,
                             tags=[tag_one, tag_two], time=two_days_ago - 60, origin=Origin.user )
            session.add_all([note, link_one, link_two, link_three, link_four, link_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
