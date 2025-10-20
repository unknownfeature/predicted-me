from backend.tests.integration.base import *
os.environ[generative_model] = 'lalalala'
import json
import unittest
from unittest.mock import patch, MagicMock


from backend.functions.recurrent.metric.units_and_aggregation.index import handler, update_metrics_in_db, prompt
from backend.lib.db import  AggregationFunction
from backend.tests.integration.base import *

mock_llm_response = [
    {"id": 1, "default_units": "lbs", "default_aggregator_function": "last",
     "default_aggregation_period_seconds": 86400},
    {"id": 3, "default_units": "count", "default_aggregator_function": "sum",
     "default_aggregation_period_seconds": 604800}
]


class TestMetricDefaultsHandler(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def tearDown(self):
        baseTearDown()

    def _setup_metrics(self):
        session = begin_session()
        try:
            user = session.get(User, legit_user_id)

            metric_1 = Metric(
                id=1, user=user, name="weight", display_name="Weight",
                default_units=None,
                default_aggregator_function=None,
                default_aggregation_period_seconds=None
            )
            metric_2 = Metric(
                id=2, user=user, name="steps", display_name="Steps",
                default_units="steps",
                default_aggregator_function=AggregationFunction.sum,
                default_aggregation_period_seconds=86400
            )
            metric_3 = Metric(
                id=3, user=user, name="pushups", display_name="Pushups",
                default_units=None,
                default_aggregator_function=None,
                default_aggregation_period_seconds=None
            )

            session.add_all([metric_1, metric_2, metric_3])
            session.commit()
        finally:
            session.close()

    @patch('backend.functions.recurrent.metric.units_and_aggregation.index.call_generative')
    def test_handler_succeeds(self, mock_call_generative):
        self._setup_metrics()
        mock_call_generative.return_value = mock_llm_response

        handler({}, {})

        session = begin_session()
        try:
            metric_1 = session.get(Metric, 1)
            metric_2 = session.get(Metric, 2)
            metric_3 = session.get(Metric, 3)

            expected_llm_input = json.dumps([
                {constants.id: 1, constants.name: "Weight"},
                {constants.id: 3, constants.name: "Pushups"}
            ])
            mock_call_generative.assert_called_once_with(
                'lalalala', prompt, expected_llm_input, 4096
            )

            assert metric_1.default_units == "lbs"
            assert metric_1.default_aggregator_function == AggregationFunction.last
            assert metric_1.default_aggregation_period_seconds == 86400

            assert metric_2.default_units == "steps"
            assert metric_2.default_aggregator_function == AggregationFunction.sum
            assert metric_2.default_aggregation_period_seconds == 86400

            assert metric_3.default_units == "count"
            assert metric_3.default_aggregator_function == AggregationFunction.sum
            assert metric_3.default_aggregation_period_seconds == 604800
        finally:
            session.close()

    @patch('backend.functions.recurrent.metric.units_and_aggregation.index.call_generative')
    def test_handler_no_metrics_to_process(self, mock_call_generative):
        self._setup_metrics()
        session = begin_session()
        try:
            m1 = session.get(Metric, 1)
            m1.default_units = 'kg'
            m1.default_aggregator_function = AggregationFunction.avg
            m1.default_aggregation_period_seconds = 86400
            m3 = session.get(Metric, 3)
            m3.default_units = 'count'
            m3.default_aggregator_function = AggregationFunction.sum
            m3.default_aggregation_period_seconds = 86400
            session.commit()
        finally:
            session.close()

        handler({}, {})

        mock_call_generative.assert_not_called()

    @patch('backend.functions.recurrent.metric.units_and_aggregation.index.call_generative')
    def test_handler_llm_returns_empty(self, mock_call_generative):
        self._setup_metrics()
        mock_call_generative.return_value = []

        handler({}, {})

        session = begin_session()
        try:
            metric_1 = session.get(Metric, 1)
            assert metric_1.default_units is None
            assert metric_1.default_aggregator_function is None
        finally:
            session.close()

    def test_update_metrics_in_db_only_updates_null_fields(self):
        self._setup_metrics()
        session = begin_session()
        try:
            metric_1 = session.get(Metric, 1)
            metric_1.default_units = "kg"
            metric_1.default_aggregator_function = AggregationFunction.avg
            session.commit()

            mock_response = [
                {"id": 1, "default_units": "lbs", "default_aggregator_function": "last",
                 "default_aggregation_period_seconds": 86400}
            ]

            update_metrics_in_db(session, mock_response)

            session = refresh_cache(session)

            metric_1_after = session.get(Metric, 1)
            assert metric_1_after.default_units == "kg"
            assert metric_1_after.default_aggregator_function == AggregationFunction.avg
            assert metric_1_after.default_aggregation_period_seconds == 86400

        finally:
            session.close()