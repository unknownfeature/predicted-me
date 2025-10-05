from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.lib.db import Note, Origin
from backend.lib.util import text_getters


def note_text_supplier(session: Session, note_id: int, origin: str):
    note_query = select(Note).where(Note.id == note_id)
    target_note = session.scalar(note_query)

    if not target_note:
        return

    return text_getters[origin](target_note)
