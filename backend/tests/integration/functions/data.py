import json
import unittest
from decimal import Decimal
from typing import Tuple

from backend.functions.data.index import handler
from backend.lib.db import Tag, Data, Origin, \
    Note, DataSchedule
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *

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

schedule_target_value = 4
schedule_units = 'testu'
schedule_recurrence = '1 * * * * *'

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

display_name = 'Some human readable metric with special characters, such as "%"'

value_one = 12.45
value_two = 11.88
value_three = 114.88

units = 'the units'
other_units = 'other units'
malicious_units = 'mal units'

class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_data_incomplete_post_returns_500(self):
        name = normalize_identifier(display_name)

        self.event[constants.body] = {
            constants.units: units,
            constants.name: display_name,

        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])['error'] == 'Internal server error'
        session = begin_session()

        try:
            assert len(get_metrics_by_display_name(display_name, session)) == 0
            assert len(get_metrics_by_name(name, session)) == 0
        finally:
            session.close()

    def test_data_post_succeeds(self):

        metric_id, data_id = self._setup_metric(display_name, value=value_one, units=units)

        session = begin_session()

        try:

            #  make sure name and display name are expected
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1

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

            self.event[constants.body] = {
                constants.value: value_two,
                constants.units: units,
            }
            self.event[constants.path_params][constants.id] = metric_id
            self.event[constants.http_method] = constants.post

            result = handler(self.event, None)

            assert result[constants.status_code] == 201
            assert json.loads(result[constants.body])[constants.id] is not None

            # new cache
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1

            metric = metrics[0]

            # should add one more
            assert len(metric.data_points) == 2
            data = metric.data_points[1]

            # and second data point got saved
            assert data.value == Decimal(str(value_two))
            assert data.units == units
            assert data.time > 0

        finally:
            session.close()

    def test_data_post_fails_for_malicious_user(self):
        metric_id, _ = self._setup_metric(display_name)

        name = normalize_identifier(display_name)

        session = begin_session()

        try:

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.post
            malicious_event[constants.query_params] = {}
            malicious_event[constants.body] = {

                constants.value: value_two,
                constants.units: units,
            }
            malicious_event[constants.path_params][constants.id] = metric_id
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1

            metric = metrics[0]

            # should add one more
            assert len(metric.data_points) == 0

            # just in case
            assert session.query(User).count() == 2


        finally:
            session.close()

    def test_data_patch_succeeds(self):

        metric_id, data_id = self._setup_metric(display_name, value=value_one, units=units)

        session = begin_session()

        try:
            #  make sure name and display name are expected
            metrics = get_metrics_by_display_name(display_name, session)

            metric = metrics[0]
            # lan of data is correct
            assert len(metric.data_points) == 1
            assert metric.id == metric_id

            data = metric.data_points[0]

            assert data.value == Decimal(str(value_one))
            assert data.units == units
            assert data.time > 0

            self.event[constants.body] = {
                constants.value: value_two,
                constants.units: other_units,
                constants.time: 25
            }
            self.event[constants.path_params][constants.id] = data_id
            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache bc sqlalchemy
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1

            metric = metrics[0]

            # should still be one
            assert len(metric.data_points) == 1
            data = metric.data_points[0]

            # but with updated fields
            assert data.value == Decimal(str(value_two))
            assert data.units == other_units
            assert data.time == 25
            assert data.id == data_id

            # just in case
            assert session.query(User).count() == 2

        finally:
            session.close()

    def test_data_patch_fails_for_malicious_user(self):
        
        metric_id, data_id = self._setup_metric(display_name, value=value_one, units=units)

        session = begin_session()

        try:

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.patch
            malicious_event[constants.query_params] = {}
            malicious_event[constants.body] = {

                constants.value: value_three,
                constants.units: malicious_units,
            }
            malicious_event[constants.path_params][constants.id] = data_id
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            # make sure new data wans't added for the malicious user
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1

            metric = metrics[0]
            assert len(metric.data_points) == 1

            data = metric.data_points[0]

            # should be old values
            assert data.value == Decimal(str(value_one))
            assert data.units == units

            # just in case
            assert session.query(User).count() == 2


        finally:
            session.close()

    def test_data_delete_succeeds(self):

        _, data_id = self._setup_metric(display_name, value=value_one, units=units)


        session = begin_session()

        try:

            self.event =  prepare_http_event(get_user_by_id(legit_user_id, session).external_id)
            self.event[constants.body] = {}
            self.event[constants.path_params][constants.id] = data_id
            self.event[constants.http_method] = constants.delete
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache
            session = refresh_cache(session)

            # make sure it didn't insert ore metrics
            metrics = get_metrics_by_display_name(display_name, session)
            assert len(metrics) == 1

            metric = metrics[0]

            # should be 0
            assert len(metric.data_points) == 0


        finally:
            session.close()

    def test_data_delete_fails_for_malicious_user(self):

        _, data_id = self._setup_metric(display_name, value=value_one, units=units)

        session = begin_session()

        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.delete
            malicious_event[constants.query_params] = {}
            malicious_event[constants.body] = {}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            session = refresh_cache(session)

            #  make sure name and display name are expected
            metrics = get_metrics_by_display_name(display_name, session)

            metric = metrics[0]
            # lan of data is correct bc it wasn't deleted
            assert len(metric.data_points) == 1

            data = metric.data_points[0]

            assert data.value == Decimal(str(value_one))
            assert data.units == units
            assert data.time > 0
           
        finally:
            session.close()
            
    def test_data_get_by_data_id_succeeds(self):

        session = begin_session()
        try:
            self._setup_data_for_search(session)
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
            assert len(items) == 2

        finally:
            session.close()

    def test_data_get_by_data_id_fails_for_malicious_user(self):

        session = begin_session()
        try:
            self._setup_data_for_search(session)
            self.event[constants.http_method] = constants.get


            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user


        finally:
            session.close()



    def test_data_get_by_note_succeeds(self):
        session = begin_session()
        try:
            self._setup_data_for_search(session)
            self.event[constants.http_method] = constants.get

            self.event[constants.query_params] = {
                constants.note_id: 1,
                # start and end will be  == now - 1 day which is outside for this particular data point but it should be ignored
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            assert items[0][constants.note_id] == 1
            assert items[0][constants.origin] == Origin.user.value

            self.event[constants.query_params] = {
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2


        finally:
            session.close()

    def test_data_get_by_note_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_data_for_search(session)

            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0  # no items for this user
        finally:
            session.close()

    def test_data_get_by_tags_display_names_succeeds(self):

        session = begin_session()
        try:
            self._setup_data_for_search(session)
            self.event[constants.http_method] = constants.get

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            ##########################################
            self.event[constants.query_params] = {
                constants.tags: f'{tag_three_display_name}|{tag_one_display_name}',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

        finally:
            session.close()

    def test_data_get_by_tags_display_names_fails_for_malicious_user(self):

        session = begin_session()
        try:
            self._setup_data_for_search(session)
            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()



    def test_data_get_by_metrics_display_name_succeeds(self):

        session = begin_session()
        try:
            self._setup_data_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.metric: metric_one_display_name,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 6

            self.event[constants.query_params] = {
                constants.metric: unique_piece,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3  # only 2nd metric's data

        finally:
            session.close()

    def test_data_get_by_metrics_display_name_fails_for_malicious_user(self):
        session = begin_session()
        try:
            self._setup_data_for_search(session)
            malicious_event = prepare_http_event(get_user_by_id(2, session).external_id)
            malicious_event[constants.http_method] = constants.get
            malicious_event[constants.query_params] = {
                constants.metric: metric_one_display_name,
                constants.start: three_days_ago - seconds_in_day,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()


    def test_data_get_by_date_succeeds(self):
        session = begin_session()
        try:

            self._setup_data_for_search(session)
            self.event[constants.http_method] = constants.get
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: three_days_ago,
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.value] == data_five_value
            assert items[1][constants.value] == data_two_value

            assert items[0][constants.metric][constants.name] == metric_two_display_name
            assert items[1][constants.metric][constants.name] == metric_one_display_name

            assert items[0][constants.metric][constants.schedule][constants.target_value] == schedule_target_value
            assert items[0][constants.metric][constants.schedule][constants.units] == schedule_units
            assert items[0][constants.metric][constants.schedule][constants.recurrence_schedule] == schedule_recurrence

            assert len(items[1][constants.metric][constants.tags]) == 2
            assert items[1][constants.metric][constants.tags][0] == tag_one_display_name
            assert items[1][constants.metric][constants.tags][1] == tag_two_display_name

            #############################################

            self.event[constants.query_params] = {}  # should default to now - 1d

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 2

            assert items[0][constants.value] == data_four_value
            assert items[1][constants.value] == data_six_value

            assert items[0][constants.metric][constants.name] == metric_two_display_name
            assert items[1][constants.metric][constants.name] == metric_two_display_name

            #############################################
            self.event[constants.query_params] = {
                constants.start: two_days_ago,
            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 3

            assert items[0][constants.value] == data_four_value
            assert items[1][constants.value] == data_six_value
            assert items[2][constants.value] == data_three_value

            assert items[0][constants.metric][constants.name] == metric_two_display_name
            assert items[1][constants.metric][constants.name] == metric_two_display_name
            assert items[2][constants.metric][constants.name] == metric_one_display_name

            ##############################################
            self.event[constants.query_params] = {
                constants.end: two_days_ago,
            }
            result = handler(self.event, None)
            items = json.loads(result[constants.body])
            assert len(items) == 1

            assert items[0][constants.value] == data_one_value
            assert items[0][constants.metric][constants.name] == metric_one_display_name

            ##############################################
            # pagination
            ##############################################

            # offset defaults to 0 and limit to 100 so all 6 return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),

            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 6

            # offset defaults to 0, limit 4 so 4 return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
                constants.limit: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 4

            # offset defaults 4, limit 100 abd we only have 6 left so 2 will return
            self.event[constants.query_params] = {
                constants.start: three_days_ago - seconds_in_day,
                constants.end: get_utc_timestamp(),
                constants.offset: 4,

            }

            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            assert len(json.loads(result[constants.body])) == 2

            assert session.query(Metric).count() == 2
            assert session.query(Data).count() == 6

        finally:
            session.close()

    def test_data_get_by_date_fails_for_malicious_user(self):
        session = begin_session()
        try:
            #  m1_d2 & m2_d5 3d |   m1_d1 2d |  m1_d3  1d | m2_d4 & m2_d6  now

            self._setup_data_for_search(session)

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

    def _setup_metric(self, display_name: str, value=None, units=None) -> Tuple[int, int|None]:
        session = begin_session()

        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)

            tag_one = Tag(name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(name=tag_two_name, display_name=tag_two_display_name)

            user = session.query(User).get(user_id)
            metric_one = Metric(name=normalize_identifier(display_name), display_name=display_name, user=user,
                                tags=[tag_one, tag_two])

            if value and units:
                metric_one.data_points.append(Data(value=value, units=units, origin=Origin.user))
            session.add(metric_one)
            session.commit()

            if value and units:
                return  metric_one.id, metric_one.data_points[0].id
            return metric_one.id, None

        finally:
            session.close()


    def _setup_data_for_search(self, session):
        user_id, external_user_id = get_user_ids_from_event(self.event, session)

        tag_one = Tag(name=tag_one_name, display_name=tag_one_display_name)
        tag_two = Tag(name=tag_two_name, display_name=tag_two_display_name)

        tag_three = Tag(name=tag_three_name, display_name=tag_three_display_name)

        user = session.query(User).get(user_id)

        assert user.external_id == external_user_id
        note = Note(user=user)
        session.add(note)
        session.flush()

        metric_one = Metric(name=metric_one_name, display_name=metric_one_display_name, user=user,
                            tags=[tag_one, tag_two])
        metric_two = Metric(name=metric_two_name, display_name=metric_two_display_name, user=user,
                            tags=[tag_two, tag_three],
                            schedule=DataSchedule(target_value=schedule_target_value, units=schedule_units,
                                                  recurrence_schedule=schedule_recurrence))
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

