from functools import reduce

import pytest

from e2e.clients import note, data
from e2e.common import wait_for_a_condition_to_be_true
from shared import constants

get_note_supplier = lambda jwt: lambda: data.get(query_params={constants.note_id: id}, jwt=jwt)
extracted_data_not_empty_predicate = lambda extracted_data: extracted_data is not None and len(extracted_data) > 0
all_tagged_predicate = lambda extracted_data: reduce(lambda one, two: one and two, map(lambda x: x[constants.metric][constants.tagged], extracted_data))


@pytest.mark.asyncio
async def test_data_extracted_from_note_text(text: str, jwt: str, attempts=3):
    id = note.create(text=text, jwt=jwt)
    stored_note = note.get(id, jwt=jwt)
    assert stored_note and stored_note[constants.text] == text
    print('*** test_data_extracted_from_note_text *** created note {}'.format(id))
    note_supplier = get_note_supplier(jwt)
    await wait_for_data_and_tags(attempts, id, note_supplier)


@pytest.mark.asyncio
async def test_data_extracted_from_audio(source_audio_key: str, jwt: str, attempts=3):
    id = note.create(audio_s3_source=source_audio_key, jwt=jwt)
    stored_note = note.get(id, jwt=jwt)
    assert stored_note and stored_note[constants.audio_key] == source_audio_key
    note_supplier = get_note_supplier(jwt)
    await wait_for_a_condition_to_be_true(lambda note: note[constants.audio_transcribed] and note[constants.audio_text], note_supplier,
                                                           f'*** test_data_extracted_from_audio *** audio was not transcribed for note {id}',
                                                           retries=attempts)
    await wait_for_data_and_tags(attempts, id, note_supplier, 'test_data_extracted_from_audio')


@pytest.mark.asyncio
async def test_data_extracted_from_image(source_image_key: str, jwt: str, attempts=3):
    id = note.create(image_s3_source=source_image_key, jwt=jwt)
    stored_note = note.get(id, jwt=jwt)
    assert stored_note and stored_note[constants.image_key] == source_image_key
    note_supplier = get_note_supplier(jwt)
    await wait_for_a_condition_to_be_true(lambda note: note[constants.image_described] and (note[constants.image_text] or  note[constants.image_description]), note_supplier,
                                                           f'*** test_data_extracted_from_image *** image wasn\'t described/text wasn\'t extracted for note {id}',
                                                           retries=attempts)
    await wait_for_data_and_tags(attempts, id, note_supplier, 'test_data_extracted_from_image')


async def wait_for_data_and_tags(attempts, id, note_supplier, test_name: str):
    await wait_for_a_condition_to_be_true(extracted_data_not_empty_predicate, note_supplier,
                                          f'*** {test_name} *** data not available for note {id}',
                                          retries=attempts)
    await wait_for_a_condition_to_be_true(all_tagged_predicate, note_supplier,
                                          f'*** {test_name} *** not all data for note has been tagged {id}',
                                          retries=attempts)
