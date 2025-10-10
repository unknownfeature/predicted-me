import unittest
import uuid

from backend.lib.db import begin_session, Note, User, Origin
from backend.lib.func.sqs import note_text_supplier
from backend.tests.integration.base import baseSetUp, baseTearDown, refresh_cache, legit_user_id


class Test(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.event = baseSetUp(None)

    def test_returns_correct_text_based_on_origin(self):
       session = begin_session()
       try:

           text_origin = 'text origin'
           audio_text_origin = 'audio text origin'
           img_desc_origin = 'img desc origin'
           img_text_origin = 'img text origin'

           note = Note(text=text_origin, audio_text=audio_text_origin, image_description=img_desc_origin,
                       image_text=img_text_origin, user_id=legit_user_id )
           session.add(note)

           session.commit()

           session = refresh_cache(session)


           assert note_text_supplier(session, 1, Origin.text) == text_origin
           assert note_text_supplier(session, 1, Origin.audio_text) == audio_text_origin
           assert note_text_supplier(session, 1, Origin.img_desc) == img_desc_origin
           assert note_text_supplier(session, 1, Origin.img_text) == img_text_origin

           assert note_text_supplier(session, 2, Origin.user) is None
       finally:
           session.close()

    def tearDown(self):
        baseTearDown()
