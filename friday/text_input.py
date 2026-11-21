"""Text typed in the window: validation and hand-over to the assistant.

TextInput is created before the assistant starts. The assistant thread sets the
handler once it is ready, so text typed during loading is rejected (the page keeps
it in the field). The text itself is never logged.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

log = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 500

TextHandler = Callable[[str], bool]


class TextInput:
    def __init__(self, max_length: int = MAX_TEXT_LENGTH) -> None:
        if max_length < 1:
            raise ValueError("max_length must be positive")
        self._max_length = max_length
        self._handler: TextHandler | None = None
        self._lock = threading.Lock()

    @property
    def max_length(self) -> int:
        return self._max_length

    def set_handler(self, handler: TextHandler | None) -> None:
        with self._lock:
            self._handler = handler

    def submit(self, text: str) -> bool:
        """Hand typed text to the assistant. True means it was accepted."""
        cleaned = text.strip()
        if not cleaned:
            return False
        if len(cleaned) > self._max_length:
            log.info("typed text rejected: too long (%d chars)", len(cleaned))
            return False
        with self._lock:
            handler = self._handler
        if handler is None:
            log.info("typed text rejected: the assistant is not ready")
            return False
        try:
            return bool(handler(cleaned))
        except Exception:
            log.exception("could not hand over typed text")
            return False
