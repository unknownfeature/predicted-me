from typing import Callable, Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import session

from backend.lib.db import Note
from backend.lib.func.base import BaseSQSTriggeredLLMClientFunction
from backend.lib.util import text_getters


def text_supplier(sss: session, note_id, origin):
    note_query = select(Note).where(Note.id == note_id)
    target_note = sss.scalar(note_query)

    if not target_note:
        return

    return text_getters[origin](target_note)

class Function(BaseSQSTriggeredLLMClientFunction):
    def __init__(self, prompt, on_extracted_cb: Callable[[session, int, str, List[Dict[str, Any]]], None],
                 generative_model: str, max_tokens: int):
        super().__init__(prompt, text_supplier, on_extracted_cb, generative_model, max_tokens)


