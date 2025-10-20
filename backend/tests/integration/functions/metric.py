import json
import unittest
from backend.tests.integration.base import *
from backend.functions.metric.index import handler
from backend.lib.util import get_user_ids_from_event
from backend.lib.db import AggregationFunction, seconds_in_day

metric_one_display_name = 'display name one'
metric_two_display_name = 'display name two'
metric_three_display_name = 'display name  three' + unique_piece
metric_four_display_name = 'display name our'
metric_five_display_name = 'display name five'


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.event = baseSetUp(Trigger.http)

    def test_incomplete_post_returns_500(self):
        self.event[constants.body] = json.dumps({})
        self.event[constants.request_context] = self.event[constants.request_context] | {
            constants.http: {constants.method: constants.post}}
        result = handler(self.event, None)
        assert result[constants.status_code] == 500
        assert json.loads(result[constants.body])[constants.error] == constants.internal_server_error
        session = begin_session()
        try:
            assert len(get_metrics_by_display_name(metric_one_display_name, session)) == 0
        finally:
            session.close()

    def test_metric_post_fails_for_duplicate(self):
        self._setup_metrics()
        session = begin_session()
        try:
            self.event[constants.body] = json.dumps({
                constants.name: metric_two_display_name,
            })
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.post}}
            result = handler(self.event, None)
            assert result[constants.status_code] == 500
        finally:
            session.close()

    def test_metric_post_succeeds_for_duplicate_from_another_user(self):
        self._setup_metrics()
        session = begin_session()
        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = json.dumps({
                constants.name: metric_two_display_name,
            })
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.post}}
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 201
            session = refresh_cache(session)
            metrics = get_metrics_by_display_name(metric_two_display_name, session)
            assert len(metrics) == 2
            assert not metrics[1].tagged
        finally:
            session.close()

    def test_metric_post_succeeds_with_new_fields(self):
        self.event[constants.body] = json.dumps({
            constants.name: metric_one_display_name,
            constants.tags: [tag_two_display_name, tag_three_display_name],
            constants.default_units: 'kg',
            constants.default_aggregator_function: 'avg',
            constants.default_aggregation_period_seconds: 3600
        })
        self.event[constants.request_context] = self.event[constants.request_context] | {
            constants.http: {constants.method: constants.post}}

        result = handler(self.event, None)
        assert result[constants.status_code] == 201
        new_id = json.loads(result[constants.body])[constants.id]
        assert new_id is not None

        session = begin_session()
        try:
            metrics = get_metrics_by_display_name(metric_one_display_name, session)
            assert len(metrics) == 1
            metric = metrics[0]
            user_id, external_id = get_user_ids_from_event(self.event, session)

            assert user_id == metric.user_id
            assert metric.user.external_id == external_id
            assert metric.tagged
            assert metric.default_units == 'kg'
            assert metric.default_aggregator_function == AggregationFunction.avg
            assert metric.default_aggregation_period_seconds == 3600
        finally:
            session.close()

    def test_metric_patch_succeeds_with_new_fields(self):
        self._setup_metrics()
        session = begin_session()
        try:
            metric = get_metrics_by_display_name(metric_one_display_name, session)[0]
            assert metric.display_name == metric_one_display_name
            assert metric.default_units == 'kg'
            assert metric.default_aggregator_function == AggregationFunction.sum
            metric_id = metric.id

            self.event[constants.body] = json.dumps({
                constants.name: metric_two_display_name + unique_piece,
                constants.tags: [tag_three_display_name],
                constants.default_units: 'lbs',
                constants.default_aggregator_function: 'count',
                constants.default_aggregation_period_seconds: 0
            })
            self.event[constants.path_params][constants.id] = metric_id
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.patch}}
            result = handler(self.event, None)
            assert result[constants.status_code] == 204

            session = refresh_cache(session)
            metric = get_metric_by_id(metric_id, session)

            assert metric.display_name == metric_two_display_name + unique_piece
            assert len(metric.tags) == 1
            assert metric.tagged
            assert metric.default_units == 'lbs'
            assert metric.default_aggregator_function == AggregationFunction.count.value
            assert metric.default_aggregation_period_seconds == 3600
        finally:
            session.close()

    def test_metric_patch_fails_for_malicious_user(self):
        self._setup_metrics()
        session = begin_session()
        try:
            metric = get_metrics_by_display_name(metric_one_display_name, session)[0]
            metric_id = metric.id

            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.body] = json.dumps({
                constants.name: metric_two_display_name,
                constants.default_units: 'hacked'
            })
            malicious_event[constants.path_params][constants.id] = metric_id
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.patch}}
            result = handler(malicious_event, None)

            assert result[constants.status_code] == 400

            session = refresh_cache(session)
            metric = get_metric_by_id(metric_id, session)
            assert metric.display_name == metric_one_display_name
            assert metric.default_units == 'kg'
        finally:
            session.close()

    def test_metric_get_by_metric_id_succeeds_and_returns_new_fields(self):
        self._setup_metrics()
        session = begin_session()
        try:
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}

            self.event[constants.path_params][constants.id] = 1
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
            metric = items[0]
            assert metric[constants.id] == 1
            assert metric[constants.default_units] == 'kg'
            assert metric[constants.default_aggregator_function] == 'sum'
            assert metric[constants.default_aggregation_period_seconds] == 3600

            self.event[constants.query_params] = {}
            self.event[constants.path_params] = {}
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 5
        finally:
            session.close()

    def test_metric_get_by_metric_id_fails_for_malicious_user(self):
        self._setup_metrics()
        session = begin_session()
        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}
            malicious_event[constants.path_params][constants.id] = 1
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0

            malicious_event[constants.query_params] = {}
            malicious_event[constants.path_params] = {}
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()

    def test_metric_get_by_tags_display_names_succeeds(self):
        self._setup_metrics()
        session = begin_session()
        try:
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}
            self.event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 4
        finally:
            session.close()

    def test_metric_get_by_tags_display_names_fails_for_malicious_user(self):
        self._setup_metrics()
        session = begin_session()
        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}
            malicious_event[constants.query_params] = {
                constants.tags: f'{tag_two_display_name}',
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()

    def test_metric_get_by_display_name_and_display_name_succeeds(self):
        self._setup_metrics()
        session = begin_session()
        try:
            self.event[constants.request_context] = self.event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}
            self.event[constants.query_params] = {
                constants.name: 'one',
            }
            result = handler(self.event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 1
        finally:
            session.close()

    def test_metric_get_by_display_name_fails_for_malicious_user(self):
        self._setup_metrics()
        session = begin_session()
        try:
            malicious_event = prepare_http_event(get_user_by_id(malicious_user_id, session).external_id)
            malicious_event[constants.request_context] = malicious_event[constants.request_context] | {
                constants.http: {constants.method: constants.get}}
            malicious_event[constants.query_params] = {
                constants.text: metric_one_display_name,
            }
            result = handler(malicious_event, None)
            assert result[constants.status_code] == 200
            items = json.loads(result[constants.body])
            assert len(items) == 0
        finally:
            session.close()

    def _setup_metrics(self):
        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            tag_one = Tag(user_id=user_id, name=tag_one_name, display_name=tag_one_display_name)
            tag_two = Tag(user_id=user_id, name=tag_two_name, display_name=tag_two_display_name)
            tag_three = Tag(user_id=user_id, name=tag_three_name, display_name=tag_three_display_name)
            user = session.query(User).get(user_id)
            assert user.external_id == external_user_id
            session.flush()

            metric_one = Metric(
                user=user, name=normalize_identifier(metric_one_display_name),
                display_name=metric_one_display_name,
                tagged=True, tags=[tag_one, tag_two],
                default_units='kg',
                default_aggregator_function=AggregationFunction.sum,
                default_aggregation_period_seconds=3600
            )
            metric_two = Metric(
                user=user, name=normalize_identifier(metric_two_display_name),
                display_name=metric_two_display_name,
                tagged=True, tags=[tag_one, tag_three]
            )
            metric_three = Metric(
                user=user, name=normalize_identifier(metric_three_display_name),
                display_name=metric_three_display_name,
                tagged=True, tags=[tag_three, tag_two]
            )
            metric_four = Metric(
                user=user, name=normalize_identifier(metric_four_display_name),
                display_name=metric_four_display_name,
                tagged=True, tags=[tag_two, tag_three]
            )
            metric_five = Metric(
                user=user, name=normalize_identifier(metric_five_display_name),
                display_name=metric_five_display_name,
                tagged=True, tags=[tag_one, tag_two]
            )
            session.add_all([metric_one, metric_two, metric_three, metric_four, metric_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()