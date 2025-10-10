import os
from unittest.mock import patch

from backend.tests.integration.functions.data import metric_one_display_name, \
    metric_two_display_name
from shared.variables import Env

os.environ[Env.max_tokens] = '1024'
os.environ[Env.generative_model] = 'lalalala'

import unittest

from backend.functions.text.metric.index import  on_response_from_model
from backend.lib.db import Origin, Data
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.event = baseSetUp(Trigger.http)

    @patch('backend.functions.text.metric.index.send_to_sns')
    def test_on_response_from_model_succeeds(self, send_to_sns_mock):
        self._setup_metrics()
        session = begin_session()
        input = {
            metric_one_display_name: [{constants.value: 3, constants.units: 'ml'}, {constants.value: 4, constants.units: 'mg'}, {constants.value: 5, constants.units: 'bpm'}],
            metric_two_display_name: [{constants.value: 7, constants.units: 'g'}, {constants.value: 466.8, constants.units: 'pt'}],

        }
        model_output = [{constants.name: k, constants.value: v[constants.value], constants.units: v[constants.units], }
                        for k, values in input.items() for v in values]


        try:

           assert len(session.query(Metric).all()) ==1

           session = refresh_cache(session)
           on_response_from_model(session, 1, Origin.img_text, model_output, )

           session = refresh_cache(session)
           assert len(session.query(Data).all()) == 5
           assert len(session.query(Metric).all()) == 2


           for k, v in input.items():
               metric = get_metrics_by_display_name(k, session)[0]
               sorted_data_from_db = sorted([f'{d.value}_{d.units}' for d in metric.data_points])
               assert sorted_data_from_db == sorted([f'{val[constants.value]:.2f}_{val[constants.units]}' for val in v ])

           send_to_sns_mock.assert_called_once_with(1)  # note id



        finally:
            session.close()

    def _setup_metrics(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            metric_one = Metric(user=user, display_name=metric_one_display_name,
                                name=normalize_identifier(metric_one_display_name))

            session.add_all([note, metric_one])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
