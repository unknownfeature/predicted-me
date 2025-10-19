import unittest
from typing import Dict

from sqlalchemy.sql.functions import count

from backend.tests.integration.base import baseSetUp, baseTearDown, refresh_cache, legit_user_id

from backend.lib.db import begin_session, Note, Origin
from backend.lib.func.sqs import note_text_supplier


class Test(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.event = baseSetUp(None)

    def test_returns_correct_text_based_on_origin(self):

        text_origin = 'text origin'
        audio_text_origin = 'audio text origin'
        img_desc_origin = 'img desc origin'
        img_text_origin = 'img text origin'
        key = 'the_key'

        text_and_image = f'{text_origin}. Image description: {img_desc_origin}. Image text: {img_text_origin}'
        audio_and_image = f'{audio_text_origin}. Image description: {img_desc_origin}. Image text: {img_text_origin}'
        image = f'Image description: {img_desc_origin}. Image text: {img_text_origin}'

        input = [
            # 0: Note has an image, but it has not been described. Should return None for all origins.
            (
            Note(text=text_origin, image_description=img_desc_origin, image_text=img_text_origin, user_id=legit_user_id,
                 image_described=False, image_key=key),
            {Origin.text.value: None, Origin.img_text.value: None, Origin.img_desc.value: None}),

            # 1: Note has text and a described image. All relevant origins should return the combined text.
            (
            Note(text=text_origin, image_description=img_desc_origin, image_text=img_text_origin, user_id=legit_user_id,
                 image_described=True, image_key=key),
            {Origin.text.value: text_and_image, Origin.img_text.value: text_and_image,
             Origin.img_desc.value: text_and_image}),

            # 2: Note has audio (not transcribed) and an undescribed image. Should return None.
            (Note(audio_text=audio_text_origin, audio_key=key, image_description=img_desc_origin,
                  image_text=img_text_origin, user_id=legit_user_id, image_described=False, image_key=key),
             {Origin.text.value: None, Origin.img_text.value: None, Origin.img_desc.value: None}),

            # 3: Note has audio (not transcribed) but a described image.
            #    - audio_text origin will return None because audio is not transcribed.
            #    - image origins will return only the image part because audio is not ready.
            (Note(audio_text=audio_text_origin, audio_key=key, image_description=img_desc_origin,
                  image_text=img_text_origin, user_id=legit_user_id, image_described=True, image_key=key),
             {Origin.audio_text.value: None, Origin.img_text.value: None, Origin.img_desc.value: None}),
            # BUG FIX HERE

            # 4: Note has transcribed audio but an undescribed image. Should return None.
            (
            Note(audio_text=audio_text_origin, audio_key=key, audio_transcribed=True, image_description=img_desc_origin,
                 image_key=key, image_text=img_text_origin, user_id=legit_user_id, image_described=False),
            {Origin.audio_text.value: None, Origin.img_text.value: None, Origin.img_desc.value: None}),

            # 5: Note has text, transcribed audio, and a described image. Function logic prefers text.
            (Note(text=text_origin, audio_text=audio_text_origin, audio_key=key, audio_transcribed=True,
                  image_description=img_desc_origin, image_key=key, image_text=img_text_origin, user_id=legit_user_id,
                  image_described=True),
             {Origin.text.value: text_and_image, Origin.audio_text.value: audio_and_image,
              Origin.img_desc.value: text_and_image}),

            # 6: Note has only transcribed audio and a described image. All origins should return audio + image.
            (
            Note(audio_text=audio_text_origin, audio_key=key, audio_transcribed=True, image_description=img_desc_origin,
                 image_key=key, image_text=img_text_origin, user_id=legit_user_id, image_described=True),
            {Origin.audio_text.value: audio_and_image, Origin.img_text.value: audio_and_image,
             Origin.img_desc.value: audio_and_image}),

            # 7: Note has only an undescribed image. Should return None.
            (Note(image_description=img_desc_origin, image_text=img_text_origin, user_id=legit_user_id, image_key=key),
             {Origin.img_desc.value: None, Origin.img_text.value: None}),

            # 8: Note has only a described image. Should return only the image text.
            (Note(image_description=img_desc_origin, image_text=img_text_origin, image_described=True, image_key=key,
                  user_id=legit_user_id),
             {Origin.img_desc.value: image, Origin.img_text.value: image}),

            # 9: Note has only text, no image. Should return only the text.
            (Note(text=text_origin, user_id=legit_user_id),
             {Origin.text.value: text_origin}),

            # 10: Note has only transcribed audio, no image. Should return only the audio text.
            (Note(audio_text=audio_text_origin, audio_transcribed=True, user_id=legit_user_id, audio_key=key),
             {Origin.audio_text.value: audio_text_origin})
        ]

        for index, (note_to_test, expected_outcomes) in enumerate(input):
            self._run_test(note_to_test, expected_outcomes, index)

    def _run_test(self, note: Note, expected_outcomes: Dict[str, str], index: int):
        print(f'running test #{index}')
        session = begin_session()

        try:
            session.add(note)

            session.commit()
            note_id = note.id

            session = refresh_cache(session)
            counter = 0
            for k, v in expected_outcomes.items():
                print(f'asserting outcome #{counter}')
                assert note_text_supplier(session, note_id, k) == v
                counter += 1


        finally:
            session.close()

    def tearDown(self):
        baseTearDown()
