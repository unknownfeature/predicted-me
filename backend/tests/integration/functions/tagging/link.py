import json
import unittest

from backend.functions.link.index import handler
from backend.lib.db import Tag, Note, Origin
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


    def _setup_links(self):

        session = begin_session()
        try:
            user_id, external_user_id = get_user_ids_from_event(self.event, session)
            user = session.query(User).get(user_id)

            assert user.external_id == external_user_id
            note = Note(user=user)
            session.add(note)
            session.flush()
            link_one = Link(note=note, user=user, url=link_one_url, description=link_one_description, time=two_days_ago - 60, origin=Origin.audio_text,
                            display_summary=link_one_summary, summary=normalize_identifier(link_one_summary))
            link_two = Link(user=user, url=link_two_url, description=link_two_description,  time=three_days_ago + 60, origin=Origin.user,
                            display_summary=link_two_summary, summary=normalize_identifier(link_two_summary))
            link_three = Link(note=note, user=user, url=link_three_url, description=link_three_description, time=day_ago - 60, origin=Origin.audio_text,
                              display_summary=link_three_summary, summary=normalize_identifier(link_three_summary))
            link_four = Link(note=note, user=user, url=link_four_url, description=link_four_description, time=get_utc_timestamp() - 60, origin=Origin.audio_text,
                             display_summary=link_four_summary, summary=normalize_identifier(link_four_summary))
            link_five = Link(user=user, url=link_five_url, description=link_five_description,  time=two_days_ago - 60, origin=Origin.user,
                             display_summary=link_five_summary, summary=normalize_identifier(link_five_summary))
            session.add_all([note, link_one, link_two, link_three, link_four, link_five])
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
