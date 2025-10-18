import unittest
from backend.tests.integration.base import *
from backend.functions.recurrent.data.purge.index import handler
from backend.lib.db import Origin, Data

from backend.tests.integration.functions.data import metric_one_name, metric_one_display_name


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
            metric = Metric(name=metric_one_name, display_name=metric_one_display_name, user_id=legit_user_id)
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
            handler(None, None)
            session = refresh_cache(session)
            metric = get_metrics_by_display_name(metric_one_display_name, session)[0]
            assert len(metric.data_points) == 1
            assert metric.data_points[0].time == two_days_ago

        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
