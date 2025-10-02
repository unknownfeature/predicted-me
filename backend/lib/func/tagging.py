from typing import Callable, Any, Dict, List

from sqlalchemy.orm import session

from backend.lib.func.base import BaseSQSTriggeredLLMClientFunction


class Function(BaseSQSTriggeredLLMClientFunction):
    def __init__(self, prompt: str, text_supplier: Callable[[session, int, str], str],
                 on_extracted_cb: Callable[[session, int, str, List[Dict[str, Any]]], None],
                 generative_model: str, max_tokens: int):
        super().__init__(prompt, text_supplier, on_extracted_cb, generative_model, max_tokens)


