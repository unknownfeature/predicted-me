import unittest
from backend.tests.integration.base import *
from backend.functions.recurrent.data.generate.index import handler
from backend.lib.db import Data
from backend.tests.integration.functions.data import metric_one_name, metric_one_display_name


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
            all = '*'
            old_next_run = get_utc_timestamp() - 1
            target_value = 44
            units = 'r'

            metric = Metric(name=metric_one_name, display_name=metric_one_display_name, user_id=legit_user_id,
                            schedule=DataSchedule(target_value=target_value, units=units, minute=all, hour=all, day_of_month=all,
                                                  month=all, day_of_week=all, next_run=old_next_run, period_seconds=60),  )
            data_one = Data(value=1, units='l', metric=metric, time=two_days_ago)
            data_two = Data(value=2, units='ll', metric=metric, time=more_than_three_months_ago,
                            )
            metric.data_points = [data_one, data_two]
            session.add(metric)
            session.commit()
            session = refresh_cache(session)

            metric = get_metrics_by_display_name(metric_one_display_name, session)[0]
            assert len(metric.data_points) == 2
            session = refresh_cache(session)
            ts_before = get_utc_timestamp()
            handler(None, None)
            session = refresh_cache(session)
            metric = get_metrics_by_display_name(metric_one_display_name, session)[0]
            assert len(metric.data_points) == 3

            generated = metric.data_points[2]

            assert generated.value == target_value
            assert generated.units == units
            assert metric.schedule.next_run != old_next_run
            assert metric.schedule.next_run >= ts_before + 60

        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
