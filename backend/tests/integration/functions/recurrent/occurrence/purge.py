import unittest

from backend.functions.recurrent.occurrence.purge.index import handler
from backend.lib.db import Origin, Occurrence
from backend.tests.integration.base import *
from backend.tests.integration.functions.occurrence import task_one_summary, task_one_display_summary


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_purge_succeeds(self):
        session = begin_session()
        try:
            time_now = get_utc_timestamp()
            more_than_three_months_ago = time_now - seconds_in_day * 31 * 3 - 1
            two_days_ago = time_now - seconds_in_day * 3 - 1
            task = Task(summary=task_one_summary, display_summary=task_one_display_summary, user_id=legit_user_id, description=task_one_display_summary)
            occurrence_one = Occurrence(priority=1,task=task, time=two_days_ago, origin=Origin.audio_text.value)
            occurrence_two = Occurrence(priority=2, task=task, time=more_than_three_months_ago,
                            origin=Origin.img_text.value)
            task.occurrences = [occurrence_one, occurrence_two]
            session.add(task)
            session.commit()
            session = refresh_cache(session)

            task = get_tasks_by_display_summary(task_one_display_summary, session)[0]
            assert len(task.occurrences) == 2
            session = refresh_cache(session)
            handler(None, None)
            session = refresh_cache(session)
            task = get_tasks_by_display_summary(task_one_display_summary, session)[0]
            assert len(task.occurrences) == 1
            assert task.occurrences[0].time == two_days_ago

        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
