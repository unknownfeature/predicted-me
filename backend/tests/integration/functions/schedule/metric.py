import json
import unittest
from backend.tests.integration.base import baseTearDown, baseSetUp, Trigger, legit_user_id, refresh_cache, \
    prepare_http_event, get_user_by_id, malicious_user_id, get_data_schedule_by_id
from backend.functions.schedule.metric.index import handler
from shared import constants
from backend.lib.db import Metric, normalize_identifier, begin_session, User, DataSchedule, get_utc_timestamp

from backend.tests.integration.functions.data import metric_one_display_name, metric_two_display_name

all = '*'
first = '1'
second = '2'


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_post_returns_500(self):
        self._setup_metric()
        self.event[constants.body] = {
            constants.minute: all,
            constants.hour: first,
            constants.day_of_month: second,
            constants.month: all,
            constants.day_of_week: first,
            constants.target_value: 3
        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])['error'] == constants.internal_server_error
        session = begin_session()

        try:
            assert len(session.query(DataSchedule).all()) == 0
        finally:
            session.close()

    def test_data_schedule_post_succeeds_and_generates_correct_next_run_for_period(self):
        self._setup_metric()
        session = begin_session()

        try:

            self.event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.target_value: 4,
                constants.units: 'ml',
                constants.period_seconds: 30,
            }
            self.event[constants.http_method] = constants.post
            self.event[constants.path_params][constants.id] = 1
            curr_ts = get_utc_timestamp()
            result = handler(self.event, None)

            assert result[constants.status_code] == 201
            id = json.loads(result[constants.body])[constants.id]
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(id, session)

            assert schedule.metric_id == 1
            assert schedule.target_value == 4
            assert schedule.units == 'ml'
            assert schedule.minute == all
            assert schedule.hour == first
            assert schedule.day_of_week == first
            assert schedule.day_of_month == second
            assert schedule.month == all
            assert schedule.next_run >= curr_ts + 30
            assert schedule.period_seconds == 30


        finally:
            session.close()

    def test_data_schedule_post_fails_for_duplicate_and_succeeds_for_a_new_one(self):
        self._setup_metric()
        session = begin_session()

        try:

            session.add(DataSchedule(target_value=3, units='ml',
                                     minute='1', hour='2', day_of_month='3',
                                     month='4', day_of_week='5', metric_id=1, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            self.event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.target_value: 4,
            }
            self.event[constants.http_method] = constants.post
            self.event[constants.path_params][constants.id] = 1
            result = handler(self.event, None)

            assert result[constants.status_code] == 500

            self.event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.target_value: 4,
                constants.units: 'ml'
            }
            self.event[constants.http_method] = constants.post
            self.event[constants.path_params][constants.id] = 2

            result = handler(self.event, None)

            assert result[constants.status_code] == 201
            id = json.loads(result[constants.body])[constants.id]
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(id, session)
            assert schedule.metric_id == 2
            assert schedule.target_value == 4
            assert schedule.units == 'ml'
            assert schedule.minute == all
            assert schedule.hour == first
            assert schedule.day_of_week == first
            assert schedule.day_of_month == second
            assert schedule.month == all
            assert schedule.next_run > 0


        finally:
            session.close()

    def test_data_schedule_post_fails_for_malicious_user(self):
        self._setup_metric()
        session = begin_session()

        try:

            session.add(DataSchedule(target_value=3, units='ml',
                                     minute='1', hour='2', day_of_month='3',
                                     month='4', day_of_week='5', metric_id=1,  next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.http_method] = constants.post
            malicious_event[constants.path_params][constants.id] = 1

            malicious_event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.target_value: 4,
            }

            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404


        finally:
            session.close()

    def test_data_schedule_patch_succeeds(self):
        self._setup_metric()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_target_value = 3
            old_metric_id = 1

            session.add(DataSchedule(target_value=old_target_value,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, metric_id=old_metric_id,  next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)

            session = refresh_cache(session)
            assert schedule.metric_id == old_metric_id
            assert schedule.target_value == old_target_value
            assert schedule.units is None
            assert schedule.minute == old_minute
            assert schedule.hour == old_hour
            assert schedule.day_of_week == old_day_of_week
            assert schedule.day_of_month == old_day_of_month
            assert schedule.month == old_month
            assert schedule.period_seconds is None
            old_next_run = schedule.next_run
            assert schedule.next_run > 0

            self.event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.target_value: 4,
                constants.units: 'ml',
                constants.period_seconds: 30
            }
            self.event[constants.path_params][constants.id] = 1
            self.event[constants.path_params][constants.metric_id] = 1

            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)

            assert schedule.metric_id == old_metric_id
            assert schedule.target_value == 4
            assert schedule.units == 'ml'
            assert schedule.minute == all
            assert schedule.hour == first
            assert schedule.day_of_week == first
            assert schedule.day_of_month == second
            assert schedule.month == all
            assert schedule.next_run != old_next_run
            assert schedule.period_seconds == 30


        finally:
            session.close()

    def test_data_schedule_patch_fails_for_malicious_user(self):
        self._setup_metric()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_target_value = 3
            old_metric_id = 1

            session.add(DataSchedule(target_value=old_target_value,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, metric_id=old_metric_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)

            session = refresh_cache(session)
            assert schedule.metric_id == old_metric_id
            assert schedule.target_value == old_target_value
            assert schedule.units is None
            assert schedule.minute == old_minute
            assert schedule.hour == old_hour
            assert schedule.day_of_week == old_day_of_week
            assert schedule.day_of_month == old_day_of_month
            assert schedule.month == old_month

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.target_value: 4,

                constants.units: 'ml'
            }
            malicious_event[constants.path_params][constants.id] = 1
            malicious_event[constants.path_params][constants.metric_id] = 1
            malicious_event[constants.http_method] = constants.patch
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)

            #  all old
            assert schedule.metric_id == old_metric_id
            assert schedule.target_value == old_target_value
            assert schedule.units is None
            assert schedule.minute == old_minute
            assert schedule.hour == old_hour
            assert schedule.day_of_week == old_day_of_week
            assert schedule.day_of_month == old_day_of_month
            assert schedule.month == old_month


        finally:
            session.close()

    def test_data_schedule_delete_succeeds(self):

        self._setup_metric()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_target_value = 3
            old_metric_id = 1

            session.add(DataSchedule(target_value=old_target_value,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, metric_id=old_metric_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)
            assert schedule.metric_id == old_metric_id

            self.event = prepare_http_event(get_user_by_id(legit_user_id, session).external_id)
            self.event[constants.body] = {}
            self.event[constants.path_params][constants.id] = 1
            self.event[constants.http_method] = constants.delete
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)
            assert schedule is None


        finally:
            session.close()

    def test_data_schedule_delete_fails_for_malicious_user(self):

        self._setup_metric()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_target_value = 3
            old_metric_id = 1

            session.add(DataSchedule(target_value=old_target_value,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, metric_id=old_metric_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)
            assert schedule.metric_id == old_metric_id

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {}
            malicious_event[constants.path_params][constants.id] = 1
            malicious_event[constants.http_method] = constants.delete
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            # new cache
            session = refresh_cache(session)

            schedule = get_data_schedule_by_id(1, session)
            assert schedule.metric_id == old_metric_id


        finally:
            session.close()

    def _setup_metric(self):
        session = begin_session()
        try:
            user = session.query(User).get(legit_user_id)
            session.add_all([Metric(user=user, name=normalize_identifier(metric_one_display_name),
                               display_name=metric_one_display_name,
                               tagged=False),
                        Metric(user=user, name=normalize_identifier(metric_two_display_name),
                               display_name=metric_two_display_name,
                               tagged=False)]
                        )
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
