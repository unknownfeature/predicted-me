import asyncio

from e2e.clients import note, data
async def test_data_extracted_from_note_text(text: str, jwt: str, attempts = 3):
    id = note.create(text=text, jwt=jwt)
    atempts_left = attempts
    while attempts > 0:
       await asyncio.sleep(1)
       data.get()