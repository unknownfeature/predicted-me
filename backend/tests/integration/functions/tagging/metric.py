import os
from backend.tests.integration.base import *
from shared.variables import *

os.environ[max_tokens] = '1024'
os.environ[generative_model] = 'lalalala'

import json
import unittest

from backend.functions.tagging.metric.index import text_supplier, on_response_from_model
from backend.lib.db import Origin, Data
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *


metric_one_name = 'name for metric one'
metric_two_name = 'name for metric two'



class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.event = baseSetUp(Trigger.http)

    def test_text_supplier_succeeds(self):
        self._setup_metrics()
        session = begin_session()
        try:
            text = text_supplier(session, 1, None)
            results = json.loads(text)
            print(results)
            assert results == [{
                constants.id: 1,
                constants.name: metric_one_name,
            }, {
                constants.id: 2,
                constants.name: metric_two_name,
            }
            ]
        finally:
            session.close()

    def test_text_supplier_returns_nothing_for_tagged_metrics(self):
        self._setup_metrics(tagged=True)
        session = begin_session()
        try:
            text = text_supplier(session, 1, None)
            assert text is None
        finally:
            session.close()

    def test_on_response_from_model_succeeds(self):
        self._setup_metrics()
        session = begin_session()
        input = {
            1: [tag_one_display_name, tag_two_display_name],
            2: [tag_two_display_name],

        }
        model_output = [{constants.id: k, constants.tags: v} for k, v in input.items()]

        try:

            all_tags_before = session.query(Tag).all()
            assert len(all_tags_before) == 0

            for id in input.keys():
                assert len(get_metric_by_id(id, session).tags) == 0

            session = refresh_cache(session)
            on_response_from_model(session, 1, None, model_output, )
            session.commit()  # this will be called by the handler

            session = refresh_cache(session)
            all_tags_after = session.query(Tag).all()
            assert len(all_tags_after) == 2

            for k, v in input.items():
                found_tags = sorted([str(tag.display_name) for tag in get_metric_by_id(k, session).tags])
                assert found_tags == sorted(v)



        finally:
            session.close()

    def _setup_metrics(self, tagged=False):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            metric_one = Metric(tagged=tagged, user=user, display_name=metric_one_name,
                                name=normalize_identifier(metric_one_name))
            metric_two = Metric(tagged=tagged, user=user, display_name=metric_two_name,
                                name=normalize_identifier(metric_two_name))

            data_one = Data(value=1, note=note, time=two_days_ago - 60,  metric=metric_one, )
            data_two = Data(value=1, note=note, time=three_days_ago + 60, metric=metric_one)
            data_three = Data(value=1, note=note, time=day_ago - 60,  metric=metric_one )
            data_four = Data(value=1, note=note, time=get_utc_timestamp() - 60,  metric=metric_two)
            data_five = Data(value=1, note=note, time=two_days_ago - 60, metric=metric_two)
            metric_one.data_points = [data_one, data_two, data_three]
            metric_two.data_points = [data_four, data_five]
            session.add_all([note, metric_one, metric_two])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
