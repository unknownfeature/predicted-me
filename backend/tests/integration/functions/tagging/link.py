import os
from shared.variables import Env

os.environ[Env.max_tokens] = '1024'
os.environ[Env.generative_model] = 'lalalala'

import json
import unittest

from backend.functions.tagging.link.index import text_supplier, on_response_from_model
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

    def test_text_supplier_succeeds(self):
        self._setup_links()
        session = begin_session()
        try:
            text = text_supplier(session, 1, None)
            results = json.loads(text)
            assert results == [{
                constants.id: 1,
                constants.description: link_one_description,
            }, {
                constants.id: 2,
                constants.description: link_two_description,
            }, {
                constants.id: 3,
                constants.description: link_three_description,
            }, {
                constants.id: 4,
                constants.description: link_four_description,
            }, {
                constants.id: 5,
                constants.description: link_five_description,
            }
            ]
        finally:
            session.close()

    def test_text_supplier_returns_nothing_for_tagged_links(self):
        self._setup_links(tagged=True)
        session = begin_session()
        try:
            text = text_supplier(session, 1, None)
            assert text is None
        finally:
            session.close()

    def test_on_response_from_model_succeeds(self):
        self._setup_links()
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
               assert len(get_link_by_id(id, session).tags) == 0

           session = refresh_cache(session)
           on_response_from_model(session, 1, None, model_output, )
           session.commit() # this will be called by the handler

           session = refresh_cache(session)
           all_tags_after = session.query(Tag).all()
           assert len(all_tags_after) == 3

           for k, v in input.items():
               found_tags = sorted([str(tag.display_name) for tag in get_link_by_id(k, session).tags])
               assert found_tags == sorted(v)



        finally:
            session.close()

    def _setup_links(self, tagged=False):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            link_one = Link(note=note, user=user, url=link_one_url, description=link_one_description,
                            time=two_days_ago - 60, origin=Origin.audio_text,
                            display_summary=link_one_summary, summary=normalize_identifier(link_one_summary),
                            tagged=tagged)
            link_two = Link(note=note, user=user, url=link_two_url, description=link_two_description,
                            time=three_days_ago + 60, origin=Origin.user,
                            display_summary=link_two_summary, summary=normalize_identifier(link_two_summary),
                            tagged=tagged)
            link_three = Link(note=note, user=user, url=link_three_url, description=link_three_description,
                              time=day_ago - 60, origin=Origin.audio_text,
                              display_summary=link_three_summary, summary=normalize_identifier(link_three_summary),
                              tagged=tagged)
            link_four = Link(note=note, user=user, url=link_four_url, description=link_four_description,
                             time=get_utc_timestamp() - 60, origin=Origin.audio_text,
                             display_summary=link_four_summary, summary=normalize_identifier(link_four_summary),
                             tagged=tagged)
            link_five = Link(user=user, note=note, url=link_five_url, description=link_five_description,
                             time=two_days_ago - 60, origin=Origin.user,
                             display_summary=link_five_summary, summary=normalize_identifier(link_five_summary),
                             tagged=tagged)
            session.add_all([note, link_one, link_two, link_three, link_four, link_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
