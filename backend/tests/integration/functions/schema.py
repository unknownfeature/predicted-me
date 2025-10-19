import unittest
from backend.tests.integration.base import *
from backend.functions.schema.index import handler
from backend.lib.db import Occurrence
from backend.tests.integration.functions.occurrence import task_one_summary, task_one_display_summary


class Test(unittest.TestCase):

    def test_generates_schema(self):
        session = begin_session()
        try:
            with self.assertRaises(Exception):
                self._create_test_data(session)

            event = {}
            event[constants.request_type] = 'some' # should not create db on this
            handler(event, None)

            with self.assertRaises(Exception):
                self._create_test_data(session)

            event[constants.request_type] = constants.create_request_type
            handler(event, None)
            session = refresh_cache(session)
            self._create_test_data(session)

        finally:
            session.close()

    def _create_test_data(self, session):
        user = User(external_id='external_id')
        time_now = get_utc_timestamp()
        more_than_three_months_ago = time_now - seconds_in_day * 31 * 3 - 1
        two_days_ago = time_now - seconds_in_day * 3 - 1
        task = Task(summary=task_one_summary, display_summary=task_one_display_summary, user=user,
                    description=task_one_display_summary)
        occurrence_one = Occurrence(priority=1, task=task, time=two_days_ago)
        occurrence_two = Occurrence(priority=2, task=task, time=more_than_three_months_ago,
                                    )
        task.occurrences = [occurrence_one, occurrence_two]
        session.add(user)
        session.commit()

    def tearDown(self):
        baseTearDown()
