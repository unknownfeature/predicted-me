import unittest
from datetime import datetime, timezone

from backend.lib.util import get_next_run_timestamp, call_generative, call_embedding
from backend.functions.text.metric.index import prompt as metric_prompt
from backend.functions.text.link.index import prompt as link_prompt
from backend.functions.text.task.index import prompt as task_prompt


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

        cron_expression = '30 9 1-7 * 1'
        base_time = int(datetime(2025, 10, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())

        next_run = get_next_run_timestamp(cron_expression, base_time, period_seconds=300)

        expected_run = int(datetime(2025, 10, 1, 12, 5, 0, tzinfo=timezone.utc).timestamp())
        assert next_run == expected_run

    def test_generative(self):
        generative_model = 'gemini-2.5-flash'

        text = """What a productive Sunday! Woke up feeling fantastic, probably a 9 out of 10. Started the day with a 3.5 mile run, which took about 30 minutes. My average heart rate was around 145 bpm. Later, I did some budgeting and saw I spent $75.40 on groceries. I should probably try to spend less next week. For dinner, I had a huge, delicious salad. Found a cool recipe at https://recipes.com/salad. My final weight before bed was 160.2 pounds. Feeling very tired but accomplished."""
        extracted_data = call_generative(generative_model, metric_prompt, text)
        print(extracted_data)
        extracted_links = call_generative(generative_model, link_prompt, text)
        print(extracted_links)
        extracted_tasks = call_generative(generative_model, task_prompt, text)
        print(extracted_tasks)

    def test_embedding(self):
        generative_model = 'gemini-embedding-001'
        text = """What a productive Sunday! Woke up feeling fantastic, probably a 9 out of 10. Started the day with a 3.5 mile run, which took about 30 minutes. My average heart rate was around 145 bpm. Later, I did some budgeting and saw I spent $75.40 on groceries. I should probably try to spend less next week. For dinner, I had a huge, delicious salad. Found a cool recipe at https://recipes.com/salad. My final weight before bed was 160.2 pounds. Feeling very tired but accomplished."""
        extracted_data = call_embedding(generative_model, text)
        print(extracted_data)
