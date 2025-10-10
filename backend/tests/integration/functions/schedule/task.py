import json
import unittest

from backend.functions.schedule.task.index import handler
from backend.lib import constants
from backend.lib.db import Task, normalize_identifier, begin_session, User, OccurrenceSchedule, get_utc_timestamp
from backend.tests.integration.base import baseTearDown, baseSetUp, Trigger, legit_user_id, refresh_cache, \
    prepare_http_event, get_user_by_id, malicious_user_id, get_occurrence_schedule_by_id

all = '*'
first = '1'
second = '2'
task_one_display_summary = 'task one summary'
task_two_display_summary = 'task two summary'

class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_post_returns_500(self):
        self._setup_task()
        self.event[constants.body] = {
            constants.minute: all,
            constants.hour: first,
            constants.day_of_month: second,
            constants.month: all,
            constants.day_of_week: first,
            constants.priority: 3
        }

        self.event[constants.http_method] = constants.post
        result = handler(self.event, None)

        assert result[constants.status_code] == 500

        assert json.loads(result[constants.body])['error'] == constants.internal_server_error
        session = begin_session()

        try:
            assert len(session.query(OccurrenceSchedule).all()) == 0
        finally:
            session.close()

    def test_occurrence_schedule_post_fails_for_duplicate_and_succeeds_for_a_new_one(self):
        self._setup_task()
        session = begin_session()

        try:

            session.add(OccurrenceSchedule(priority=3,
                                     minute='1', hour='2', day_of_month='3',
                                     month='4', day_of_week='5', task_id=1, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            self.event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.priority: 4,
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
                constants.priority: 4,
            }
            self.event[constants.http_method] = constants.post
            self.event[constants.path_params][constants.id] = 2

            result = handler(self.event, None)

            assert result[constants.status_code] == 201
            id = json.loads(result[constants.body])[constants.id]
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(id, session)
            assert schedule.task_id == 2
            assert schedule.priority == 4
            assert schedule.minute == all
            assert schedule.hour == first
            assert schedule.day_of_week == first
            assert schedule.day_of_month == second
            assert schedule.month == all
            assert schedule.next_run > 0


        finally:
            session.close()

    def test_occurrence_schedule_post_fails_for_malicious_user(self):
        self._setup_task()
        session = begin_session()

        try:

            session.add(OccurrenceSchedule(priority=3,
                                     minute='1', hour='2', day_of_month='3',
                                     month='4', day_of_week='5', task_id=1, next_run=get_utc_timestamp()))
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
                constants.priority: 4,
            }

            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404


        finally:
            session.close()

    def test_occurrence_schedule_patch_succeeds(self):
        self._setup_task()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_priority = 3
            old_task_id = 1

            session.add(OccurrenceSchedule(priority=old_priority,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, task_id=old_task_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)

            session = refresh_cache(session)
            assert schedule.task_id == old_task_id
            assert schedule.priority == old_priority
            assert schedule.minute == old_minute
            assert schedule.hour == old_hour
            assert schedule.day_of_week == old_day_of_week
            assert schedule.day_of_month == old_day_of_month
            assert schedule.month == old_month

            self.event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.priority: 4,
            }
            self.event[constants.path_params][constants.id] = 1
            self.event[constants.path_params][constants.task_id] = 1
            self.event[constants.http_method] = constants.patch
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)

            assert schedule.task_id == old_task_id
            assert schedule.priority == 4
            assert schedule.minute == all
            assert schedule.hour == first
            assert schedule.day_of_week == first
            assert schedule.day_of_month == second
            assert schedule.month == all
            assert schedule.next_run > 0

        finally:
            session.close()

    def test_occurrence_schedule_patch_fails_for_malicious_user(self):
        self._setup_task()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_priority = 3
            old_task_id = 1

            session.add(OccurrenceSchedule(priority=old_priority,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, task_id=old_task_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)

            session = refresh_cache(session)
            assert schedule.task_id == old_task_id
            assert schedule.priority == old_priority
            assert schedule.minute == old_minute
            assert schedule.hour == old_hour
            assert schedule.day_of_week == old_day_of_week
            assert schedule.day_of_month == old_day_of_month
            assert schedule.month == old_month
            old_next_run = schedule.next_run
            assert schedule.next_run > 0

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {
                constants.minute: all,
                constants.hour: first,
                constants.day_of_month: second,
                constants.month: all,
                constants.day_of_week: first,
                constants.priority: 4,
            }
            malicious_event[constants.path_params][constants.id] = 1
            malicious_event[constants.path_params][constants.task_id] = 1
            malicious_event[constants.http_method] = constants.patch
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)

            #  all old
            assert schedule.task_id == old_task_id
            assert schedule.priority == old_priority
            assert schedule.minute == old_minute
            assert schedule.hour == old_hour
            assert schedule.day_of_week == old_day_of_week
            assert schedule.day_of_month == old_day_of_month
            assert schedule.month == old_month
            assert schedule.next_run == old_next_run


        finally:
            session.close()

    def test_occurrence_schedule_delete_succeeds(self):

        self._setup_task()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_priority = 3
            old_task_id = 1

            session.add(OccurrenceSchedule(priority=old_priority,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, task_id=old_task_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)
            assert schedule.task_id == old_task_id

            self.event = prepare_http_event(get_user_by_id(legit_user_id, session).external_id)
            self.event[constants.body] = {}
            self.event[constants.path_params][constants.id] = 1
            self.event[constants.http_method] = constants.delete
            result = handler(self.event, None)

            assert result[constants.status_code] == 204

            # new cache
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)
            assert schedule is None


        finally:
            session.close()

    def test_occurrence_schedule_delete_fails_for_malicious_user(self):

        self._setup_task()
        session = begin_session()

        try:

            old_minute = '1'
            old_hour = '2'
            old_day_of_month = '3'
            old_month = '4'
            old_day_of_week = '*'
            old_priority = 3
            old_task_id = 1

            session.add(OccurrenceSchedule(priority=old_priority,
                                     minute=old_minute, hour=old_hour, day_of_month=old_day_of_month,
                                     month=old_month, day_of_week=old_day_of_week, task_id=old_task_id, next_run=get_utc_timestamp()))
            session.commit()
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)
            assert schedule.task_id == old_task_id

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = {}
            malicious_event[constants.path_params][constants.id] = 1
            malicious_event[constants.http_method] = constants.delete
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 404

            # new cache
            session = refresh_cache(session)

            schedule = get_occurrence_schedule_by_id(1, session)
            assert schedule.task_id == old_task_id


        finally:
            session.close()

    def _setup_task(self):
        session = begin_session()
        try:
            user = session.query(User).get(legit_user_id)
            session.add_all([Task(user=user, summary=normalize_identifier(task_one_display_summary),
                               display_summary=task_one_display_summary, description=task_one_display_summary,
                               tagged=False),
                        Task(user=user, summary=normalize_identifier(task_two_display_summary),
                               display_summary=task_two_display_summary, description=task_two_display_summary,
                               tagged=False)]
                        )
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
