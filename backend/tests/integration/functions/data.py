import json
import unittest
from decimal import Decimal

from backend.functions.data.index import handler
from backend.lib.db import begin_session, Metric, normalize_identifier, User, Tag, get_utc_timestamp, Data, Origin, \
    Note
from backend.lib.func import constants
from backend.lib.util import get_user_ids_from_event, seconds_in_day
from backend.tests.integration.base import Trigger, baseSetUp, get_metrics_by_display_name, \
    get_metrics_by_name, baseTearDown, prepare_http_event

# test data
tag_one_display_name = 'tag one Test 4^'
tag_two_display_name = 'tag & two_ la la'
tag_three_display_name = 'tag ^ three ??'

tag_one_name = normalize_identifier(tag_one_display_name)
tag_two_name = normalize_identifier(tag_two_display_name)
tag_three_name = normalize_identifier(tag_three_display_name)

metric_one_display_name = 'Some metric with special characters, such as "%" 1'
metric_one_name = normalize_identifier(metric_one_display_name)
metric_two_display_name = 'Some metric with special characters, such as "%" 2 and a unique piece'
metric_two_name = normalize_identifier(metric_two_display_name)

time_now = get_utc_timestamp()
day_ago = time_now - seconds_in_day
two_days_ago = time_now - seconds_in_day * 2
three_days_ago = time_now - seconds_in_day * 3

data_one_value = 4.5
data_two_value = 38.5
data_three_value = 100.5
data_four_value = 5678.5
data_five_value = 45.5
data_six_value = 78

data_one_units = 'u1'
data_two_units = 'u2'
data_three_units = 'u3'
data_four_units = 'u4'
data_five_units = 'u5'
data_six_units = 'u6'


class DataTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_data_post_returns_500(self):
        display_name = 'Some human readable metric with special characters, such as "%"'
        name = normalize_identifier(display_name)
        units = 'the units'

        self.event['body'] = {
            'units': units,
            'name': display_name,

        }

        self.event['httpMethod'] = 'POST'
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result['body'])['error'] == 'Internal server error'
        session = begin_session()

        try:
            assert len(get_metrics_by_display_name(display_name, session)) == 0
            assert len(get_metrics_by_name(name, session)) == 0
        finally:
            session.close()

    def test_data_post(self):

        display_name = 'Some human readable metric with special characters, such as "%"'
        name = normalize_identifier(display_name)
        value_one = 12.45
        value_two = 11.88
        units = 'the units'

        self.event['body'] = {
            'value': value_one,
            'units': units,
            'name': display_name,
        }
        self.event['httpMethod'] = 'POST'
        result = handler(self.event, None)

        assert result[constants.status_code] == 201

        session = begin_session()

        try:

            #  make sure name and display name are expected
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1 and len(get_metrics_by_name(name, session)) == 1

            metric = metrics[0]

            user_id, external_id = get_user_ids_from_event(self.event, session)

            # make sure user is correct
            assert user_id == metric.user_id
            assert metric.user.external_id == external_id

            # lan of data is correct
            assert len(metric.data_points) == 1

            data = metric.data_points[0]

            assert data.value == Decimal(str(value_one))
            assert data.units == units
            assert data.time > 0

            self.event['body'] = {
                'value': value_two,
                'units': units,
                'name': display_name,
                'metric_id': metric.id,
            }
            self.event['httpMethod'] = 'POST'
            result = handler(self.event, None)

            assert result[constants.status_code] == 201

            # new cache
            session.close()

            session = begin_session()

            # make sure it didn't insert ore metrics
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1 and len(get_metrics_by_name(name, session)) == 1

            metric = metrics[0]

            # should add one more
            assert len(metric.data_points) == 2
            data = metric.data_points[1]

            # and second data point got saved
            assert data.value == Decimal(str(value_two))
            assert data.units == units
            assert data.time > 0

            # just in case
            assert session.query(User).count() == 2


        finally:
            session.close()

    def test_data_get_by_data_id(self):

        session = begin_session()
        try:
            self.setup_data_for_search(session)
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.path_params]['id'] = 1
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            assert items[0]['id'] == 1

            ##########################################
            self.event[constants.query_params] = {}
            self.event[constants.path_params] = {}
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            #  and to check that the other user has no access
            ##########################################

            malicious_event = prepare_http_event(session.query(User).get(2).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}
            malicious_event[constants.path_params]['id'] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0 # no items for this user

        finally:
            session.close()

    def test_data_get_by_note(self):
        session = begin_session()
        try:
            self.setup_data_for_search(session)
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                'note_id': 1, # start and end will be  == now - 1 day which is outside for this particular data point but it should be ignored
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            assert items[0]['note_id'] == 1

            ##########################################
            self.event[constants.query_params] = {
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

        finally:
            session.close()


    def test_data_get_by_tags_display_names(self):

        session = begin_session()
        try:
            self.setup_data_for_search(session)
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                'tags': f'{tag_two_display_name}',
                'start': three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            ##########################################
            self.event[constants.query_params] = {
                'tags': f'{tag_three_display_name}|{tag_one_display_name}',
                'start': three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

        finally:
            session.close()

    def test_data_get_by_metrics_display_name(self):

        session = begin_session()
        try:
            self.setup_data_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                'metric': metric_one_display_name,
                'start': three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            self.event[constants.query_params] = {
                'metric': 'unique piece',
                'start': three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3  # only 2nd metric's data

        finally:
            session.close()

    def test_data_get_by_date(self):

        session = begin_session()
        try:
            #  m1_d2 & m2_d5 3d |   m1_d1 2d |  m1_d3  1d | m2_d4 & m2_d6  now
            self.setup_data_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                'start': three_days_ago - seconds_in_day,
                'end': three_days_ago,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0]['value'] == data_five_value
            assert items[1]['value'] == data_two_value

            assert items[0]['metric']['name'] == metric_two_display_name
            assert items[1]['metric']['name'] == metric_one_display_name

            #############################################

            self.event[constants.query_params] = {}  # should default to now - 1d

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0]['value'] == data_four_value
            assert items[1]['value'] == data_six_value

            assert items[0]['metric']['name'] == metric_two_display_name
            assert items[1]['metric']['name'] == metric_two_display_name

            #############################################
            self.event[constants.query_params] = {
                'start': two_days_ago,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0]['value'] == data_four_value
            assert items[1]['value'] == data_six_value
            assert items[2]['value'] == data_three_value

            assert items[0]['metric']['name'] == metric_two_display_name
            assert items[1]['metric']['name'] == metric_two_display_name
            assert items[2]['metric']['name'] == metric_one_display_name

            ##############################################
            self.event[constants.query_params] = {
                'end': two_days_ago,
            }
            result = handler(self.event, None)
            items = json.loads(result[constants.body])
            assert len(items) == 1

            assert items[0]['value'] == data_one_value
            assert items[0]['metric']['name'] == metric_one_display_name

            assert session.query(Metric).count() == 2
            assert session.query(Data).count() == 6


        finally:
            session.close()

    def setup_data_for_search(self, session):
        user_id, external_user_id = get_user_ids_from_event(self.event, session)

        tag_one = Tag(name=tag_one_name, display_name=tag_one_display_name)
        tag_two = Tag(name=tag_two_name, display_name=tag_two_display_name)

        tag_three = Tag(name=tag_three_name, display_name=tag_three_display_name)

        user = session.query(User).get(user_id)

        assert user.external_id == external_user_id
        note = Note(user=user)

        metric_one = Metric(name=metric_one_name, display_name=metric_one_display_name, user=user,
                            tags=[tag_one, tag_two])
        metric_two = Metric(name=metric_two_name, display_name=metric_two_display_name, user=user,
                            tags=[tag_two, tag_three])
        # m1_d2 & m2_d5 3d  m1_d1 2d  m1_d3  1d  m2_d4 & m2_d6  now

        metric_one.data_points.extend(
            [Data(value=data_one_value, units=data_one_units, time=three_days_ago + 60, origin=Origin.user),
             Data(value=data_two_value, units=data_two_units, time=three_days_ago - 60, origin=Origin.user),
             Data(value=data_three_value, units=data_three_units,
                  time=two_days_ago + 60, origin=Origin.user, note=note), ])
        metric_two.data_points.extend(
            [Data(value=data_four_value, units=data_four_units, time=day_ago + 60, origin=Origin.user),
             Data(value=data_five_value, units=data_five_units, time=three_days_ago - 60, origin=Origin.user),
             Data(value=data_six_value, units=data_six_units, time=day_ago + 60, origin=Origin.user), ])
        session.add_all([note, metric_one, metric_two])
        session.commit()

    def tearDown(self):
        baseTearDown()


