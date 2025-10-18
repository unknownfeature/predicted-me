import os
from unittest.mock import patch
from backend.tests.integration.base import *
from shared.variables import *

os.environ[max_tokens] = '1024'
os.environ[generative_model] = 'lalalala'

import unittest

from backend.functions.text.link.index import  on_response_from_model
from backend.lib.db import Origin
from backend.lib.util import get_user_ids_from_event
from backend.tests.integration.base import *

link_one_url = 'http://one'
link_two_url = 'http://two'
link_three_url = 'http://three/' + unique_piece
link_four_url = 'http://four'
link_five_url = 'http://five'

link_one_description = 'description for link one'
link_two_description = 'description for link two'
link_three_description = 'description for link three'
link_four_description = 'description for link four'
link_five_description = 'description for link five ' + unique_piece

link_one_summary = 'summary for link one'
link_two_summary = 'summary for link two'
link_three_summary = 'summary for link three'
link_four_summary = 'summary for link four'
link_five_summary = 'summary for link five ' + unique_piece


class Test(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.event = baseSetUp(Trigger.http)

    @patch('backend.functions.text.link.index.send_to_sns')
    def test_on_response_from_model_succeeds(self, send_to_sns_mock):
        self._setup_links()
        session = begin_session()
        input = {
            link_one_url: link_one_description,
            link_two_url: link_two_description,
            link_three_url: link_three_description,
            link_four_url: link_four_description,
            link_five_url: link_five_description,
        }
        model_output = [{constants.url: k, constants.description: v, constants.summary: k + constants.summary} for k, v in input.items()]


        try:

           assert len(session.query(Link).all()) ==1

           session = refresh_cache(session)
           on_response_from_model(session, 1, model_output, )

           session = refresh_cache(session)
           assert len(session.query(Link).all()) == 5

           for k, v in input.items():
               link = get_links_by_url(k, session)[0]
               if k == link_one_url:
                   assert link.display_summary != k  + constants.summary
               else:
                   assert link.display_summary == k + constants.summary
                   assert link.description == v

           send_to_sns_mock.assert_called_once_with(1)  # note id



        finally:
            session.close()

    def _setup_links(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            link_one = Link(note=note, user=user, url=link_one_url, description=link_one_description,
                            time=two_days_ago - 60,
                            display_summary=link_one_summary, summary=normalize_identifier(link_one_summary))

            session.add_all([note, link_one])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
