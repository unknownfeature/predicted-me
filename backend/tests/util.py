import unittest
from datetime import datetime, timezone

from backend.lib.util import get_next_run_timestamp


class Test(unittest.TestCase):

    def test_generate_next_time_succeeds(self):
        cron_expression = '0 * * * *'
        base_time = int(datetime(2025, 10, 10, 10, 30, 0, tzinfo=timezone.utc).timestamp())

        next_run = get_next_run_timestamp(cron_expression, base_time)

        expected_run = int(datetime(2025, 10, 10, 11, 0, 0, tzinfo=timezone.utc).timestamp())
        assert next_run == expected_run

        cron_expression = '0 5 * * *'
        base_time = int(datetime(2025, 10, 10, 10, 30, 0, tzinfo=timezone.utc).timestamp())

        next_run = get_next_run_timestamp(cron_expression, base_time)

        expected_run = int(datetime(2025, 10, 11, 5, 0, 0, tzinfo=timezone.utc).timestamp())
        assert next_run == expected_run

        cron_expression = '0 0 * * *'
        base_time = int(datetime(2025, 10, 10, 23, 59, 0, tzinfo=timezone.utc).timestamp())

        next_run = get_next_run_timestamp(cron_expression, base_time)

        expected_run = int(datetime(2025, 10, 11, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        assert next_run == expected_run

        cron_expression = '0 10 * * *'
        base_time = int(datetime(2025, 10, 10, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        next_run = get_next_run_timestamp(cron_expression, base_time)

        expected_run = int(datetime(2025, 10, 11, 10, 0, 0, tzinfo=timezone.utc).timestamp())
        assert next_run == expected_run

        cron_expression = '30 9 1-7 * 1'
        base_time = int(datetime(2025, 10, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())

        next_run = get_next_run_timestamp(cron_expression, base_time)

        expected_run = int(datetime(2025, 10, 2, 9, 30, 0, tzinfo=timezone.utc).timestamp())
        assert next_run == expected_run
