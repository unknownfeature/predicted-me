import unittest
from backend.tests.integration.base import *

from backend.functions.recurrent.occurrence.generate.index import handler
from backend.lib.db import  Occurrence
from backend.tests.integration.functions.occurrence import task_one_summary, task_one_display_summary


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_generate_succeeds(self):
        session = begin_session()
        try:
            time_now = get_utc_timestamp()
            more_than_three_months_ago = time_now - seconds_in_day * 31 * 3 - 1
            two_days_ago = time_now - seconds_in_day * 3 - 1
            old_next_run = get_utc_timestamp() - 1
            priority = 7
            all = '*'
            task = Task(summary=task_one_summary, display_summary=task_one_display_summary, user_id=legit_user_id, description=task_one_display_summary, schedule=OccurrenceSchedule(priority=priority, minute=all, hour=all, day_of_month=all,
                                                  month=all, day_of_week=all, next_run=old_next_run), )
            occurrence_one = Occurrence(priority=1,task=task, time=two_days_ago)
            occurrence_two = Occurrence(priority=2, task=task, time=more_than_three_months_ago,
                            )
            task.occurrences = [occurrence_one, occurrence_two]
            session.add(task)
            session.commit()
            session = refresh_cache(session)
            task = get_tasks_by_display_summary(task_one_display_summary, session)[0]
            assert len(task.occurrences) == 2
            session = refresh_cache(session)
            ts_before = get_utc_timestamp()
            handler(None, None)
            session = refresh_cache(session)
            task = get_tasks_by_display_summary(task_one_display_summary, session)[0]
            assert len(task.occurrences) == 3

            generated = task.occurrences[2]

            assert generated.priority == priority
            assert task.schedule.next_run != old_next_run
            assert task.schedule.next_run >= ts_before + 60
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
