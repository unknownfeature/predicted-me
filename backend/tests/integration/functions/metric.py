import json
import unittest

from backend.functions.metric.index import handler
from backend.lib.db import Tag
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *

metric_one_display_name = 'display name one'
metric_two_display_name = 'display name two'
metric_three_display_name = 'display name  three' + unique_piece
metric_four_display_name = 'display name our'
metric_five_display_name = 'display name five'


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
            assert len(get_metrics_by_display_name(metric_one_display_name, session)) == 0
        finally:
            session.close()

    def test_metric_post_fails_for_duplicate(self):

        self._setup_metrics()
        session = begin_session()

        try:

            self.event[constants.body] = {
                constants.name: metric_two_display_name,
            }
            self.event[constants.http_method] = constants.post
            result = handler(self.event, None)

            assert result[constants.status_code] == 500


        finally:
            session.close()

    def test_metric_post_succeeds_for_duplicate_from_another_user(self):

         self._setup_metrics()
         session = begin_session()

         try:
             malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
             malicious_event[constants.body] = {
                 constants.name: metric_two_display_name,
             }
             malicious_event[constants.http_method] = constants.post
             result = handler(malicious_event, None)

             assert result[constants.status_code] == 201

             session = refresh_cache(session)

             assert len(get_metrics_by_display_name(metric_two_display_name, session)) == 2


         finally:
             session.close()

    def test_metric_post_succeeds(self):

        self.event[constants.body] = {
            constants.name: metric_one_display_name,
        }

        self.event[constants.http_method] = constants.post

        result = handler(self.event, None)
        assert result[constants.status_code] == 201
        assert json.loads(result[constants.body])[constants.id] is not None

        session = begin_session()

        try:

            metrics = get_metrics_by_display_name(metric_one_display_name, session)
            assert len(metrics) == 1

            user = metrics[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure user is correct
            assert user_id == user.user_id
            assert user.user.external_id == external_id


        finally:
            session.close()

    def test_metric_patch_succeeds(self):
        self._setup_metrics()

        session = begin_session()

        try:

            metrics = get_metrics_by_display_name(metric_one_display_name, session)

            assert len(metrics) == 1
            metric = metrics[0]

            assert metric.display_name == metric_one_display_name
            assert len(metric.tags) == 2

            old_tag_names = [tag.display_name for tag in metric.tags]
            assert tag_one_display_name in old_tag_names
            assert tag_two_display_name in old_tag_names
            metric_id = metric.id

            new_tag_name = 'new_tag'
            self.event[constants.body] = {
                constants.name: metric_two_display_name + unique_piece,
                #  one exists and one new, both should replace old ones
                constants.tags: [new_tag_name, tag_three_display_name]
            }
            self.event[constants.path_params][constants.id] = metric_id
            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            metric = get_metric_by_id(metric_id, session)

            # but with updated fields
            assert metric.display_name == metric_two_display_name + unique_piece
            assert len(metric.tags) == 2

            new_tag_names = [tag.display_name for tag in metric.tags]
            assert new_tag_name in new_tag_names
            assert tag_three_display_name in new_tag_names

            #  make sure new tag was added and old tags were
            assert session.query(Tag).count() == 4

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()

    def test_metric_patch_fails_for_malicious_user(self):

        self._setup_metrics()
        session = begin_session()

        try:

            metrics = get_metrics_by_display_name(metric_one_display_name, session)

            assert len(metrics) == 1
            metric = metrics[0]

            assert metric.display_name == metric_one_display_name

            metric_id = metric.id

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {
                constants.name: metric_two_display_name,
            }
            malicious_event[constants.path_params][constants.id] = metric_id
            malicious_event[constants.http_method] = constants.patch
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 400

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            metric = get_metric_by_id(metric_id, session)

            # but with updated fields
            assert metric.display_name == metric_one_display_name

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()


    def test_metric_get_by_metric_id_succeeds(self):

        self._setup_metrics()

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
            assert len(items) == 5 # all of them

        finally:
            session.close()

    def test_metric_get_by_metric_id_fails_for_malicious_user(self):

        self._setup_metrics()

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


    def test_metric_get_by_tags_display_names_succeeds(self):

        self._setup_metrics()

        session = begin_session()

        try:
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 4

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5

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

            assert session.query(Metric).count() == 5

        finally:
            session.close()

    def test_metric_get_by_tags_display_names_fails_for_malicious_user(self):

        self._setup_metrics()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',

            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            ##########################################
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

        finally:
            session.close()

    def test_metric_get_by_display_name_and_display_name_succeeds(self):

        self._setup_metrics()

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
            prev_metric_id = items[0][constants.id]

            self.event[constants.query_params] = {
                constants.name: unique_piece,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1  # in display_name
            this_metric_id = items[0][constants.id]

            assert prev_metric_id != this_metric_id

        finally:
            session.close()

    def test_metric_get_by_display_name_fails_for_malicious_user(self):
        self._setup_metrics()

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.text: metric_one_display_name,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0


        finally:
            session.close()

    def _setup_metrics(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(user_id=user_id, name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(user_id=user_id, name=tag_two_name, display_name=tag_two_display_name)

            tag_three = Tag(user_id=user_id, name=tag_three_name, display_name=tag_three_display_name)

            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
        
            session.flush()
            metric_one = Metric(user=user, name=normalize_identifier(metric_one_display_name), display_name=metric_one_display_name,
                            tagged=True,
                            tags=[tag_one, tag_two])
            metric_two = Metric(user=user, name=normalize_identifier(metric_two_display_name), display_name=metric_two_display_name, 
                            tagged=True,
                            tags=[tag_one, tag_three])
            metric_three = Metric( user=user, name=normalize_identifier(metric_three_display_name), display_name=metric_three_display_name,
                              tagged=True,
                              tags=[tag_three, tag_two])
            metric_four = Metric( user=user, name=normalize_identifier(metric_four_display_name), display_name=metric_four_display_name,
                             tagged=True,
                             tags=[tag_two, tag_three])
            metric_five = Metric(user=user, name=normalize_identifier(metric_five_display_name), display_name=metric_five_display_name, 
                             tagged=True,
                             tags=[tag_one, tag_two])
            session.add_all([metric_one, metric_two, metric_three, metric_four, metric_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
