import os
from unittest.mock import patch


from shared.variables import Env

os.environ[Env.max_tokens] = '1024'
os.environ[Env.generative_model] = 'lalalala'

import unittest

from backend.functions.text.task.index import  on_extracted_cb
from backend.lib.db import Origin, Occurrence
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *



task_one_description = 'description for task one'
task_two_description = 'description for task two'
task_three_description = 'description for task three'
task_four_description = 'description for task four'
task_five_description = 'description for task five ' + unique_piece

task_one_summary = 'summary for task one'
task_two_summary = 'summary for task two'
task_three_summary = 'summary for task three'
task_four_summary = 'summary for task four'
task_five_summary = 'summary for task five ' + unique_piece


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.event = baseSetUp(Trigger.http)

    @patch('backend.functions.text.task.index.send_to_sns')
    def test_on_extracted_cb_succeeds(self, send_to_sns_mock):
        self._setup_tasks()
        session = begin_session()
        input = {
            task_one_summary: [{constants.description: 'one', constants.priority: 1}, {constants.description: 'two', constants.priority: 2}, {constants.description: 'three', constants.priority: 3}],
            task_two_summary: [{constants.description: 'four', constants.priority: 4}, {constants.description: 'five', constants.priority: 5}],

        }
        model_output = [{constants.name: k, constants.value: v[constants.value], constants.units: v[constants.units], }
                        for k, values in input.items() for v in values]


        try:

           assert len(session.query(Task).all()) ==1

           session = refresh_cache(session)
           on_extracted_cb(session, 1, Origin.img_text, model_output, )

           session = refresh_cache(session)
           assert len(session.query(Occurrence).all()) == 5
           assert len(session.query(Task).all()) == 2


           for k, v in input.items():
               task = get_tasks_by_display_summary(k, session)[0]
               sorted_data_from_db = sorted([f'{d.priority}_{d.description}' for d in task.occurrences])

               if k == task_one_summary:
                   assert sorted_data_from_db == sorted(
                       [f'{val[constants.priority]}_{task_one_description}' for val in v])
               else:
                  assert sorted_data_from_db == sorted([f'{val[constants.priority]}_{val[constants.description]}' for val in v ])

           send_to_sns_mock.assert_called_once_with(1)  # note id



        finally:
            session.close()

    def _setup_tasks(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            task_one = Task(user=user, display_summary=task_one_summary,
                                summary=normalize_identifier(task_one_summary), description=task_one_description)

            session.add_all([note, task_one])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
