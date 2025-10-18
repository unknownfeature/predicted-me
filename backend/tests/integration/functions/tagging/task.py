import os
from backend.tests.integration.base import *
from shared.variables import *

os.environ[max_tokens] = '1024'
os.environ[generative_model] = 'lalalala'

import json
import unittest

from backend.functions.tagging.task.index import text_supplier, on_response_from_model
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

    def test_text_supplier_succeeds(self):
        self._setup_tasks()
        session = begin_session()
        try:
            text = text_supplier(session, 1, None)
            results = json.loads(text)
            assert results == [{
                constants.id: 1,
                constants.description: task_one_description,
            }, {
                constants.id: 2,
                constants.description: task_two_description,
            }, {
                constants.id: 3,
                constants.description: task_three_description,
            }, {
                constants.id: 4,
                constants.description: task_four_description,
            }, {
                constants.id: 5,
                constants.description: task_five_description,
            }
            ]
        finally:
            session.close()

    def test_text_supplier_returns_nothing_for_tagged_tasks(self):
        self._setup_tasks(tagged=True)
        session = begin_session()
        try:
            text = text_supplier(session, 1, None)
            assert text is None
        finally:
            session.close()

    def test_on_response_from_model_succeeds(self):
        self._setup_tasks()
        session = begin_session()
        input = {
            1: [tag_one_display_name, tag_two_display_name],
            2: [tag_two_display_name],
            3: [tag_one_display_name, tag_three_display_name],
            4: [tag_three_display_name],
            5: [tag_two_display_name, tag_three_display_name],
        }
        model_output = [{constants.id: k, constants.tags: v} for k, v in input.items()]


        try:

           all_tags_before = session.query(Tag).all()
           assert len(all_tags_before) == 0


           for id in input.keys():
               assert len(get_task_by_id(id, session).tags) == 0

           session = refresh_cache(session)
           on_response_from_model(session, 1, None, model_output, )
           session.commit() # this will be called by the handler

           session = refresh_cache(session)
           all_tags_after = session.query(Tag).all()
           assert len(all_tags_after) == 3

           for k, v in input.items():
               found_tags = sorted([str(tag.display_name) for tag in get_task_by_id(k, session).tags])
               assert found_tags == sorted(v)



        finally:
            session.close()

    def _setup_tasks(self, tagged=False):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            task_one = Task(note=note, user=user, description=task_one_description,
                            display_summary=task_one_summary, summary=normalize_identifier(task_one_summary),
                            tagged=tagged)
            task_two = Task(note=note, user=user, description=task_two_description,
                            display_summary=task_two_summary, summary=normalize_identifier(task_two_summary),
                            tagged=tagged)
            task_three = Task(note=note, user=user, description=task_three_description,
                              display_summary=task_three_summary, summary=normalize_identifier(task_three_summary),
                              tagged=tagged)
            task_four = Task(note=note, user=user,  description=task_four_description,
                             display_summary=task_four_summary, summary=normalize_identifier(task_four_summary),
                             tagged=tagged)
            task_five = Task(user=user, note=note,  description=task_five_description,
                             display_summary=task_five_summary, summary=normalize_identifier(task_five_summary),
                             tagged=tagged)
            session.add_all([note, task_one, task_two, task_three, task_four, task_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
