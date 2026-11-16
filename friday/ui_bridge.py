"""Bridge: turns UI events into JavaScript calls for the window.

Events that arrive before the page has loaded are queued and flushed in order.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Callable

from friday.ui_events import MessageAdded, StateChanged, UiEvent

logger = logging.getLogger(__name__)


class UiBridge:
    def __init__(self, evaluate_js: Callable[[str], object]) -> None:
        self._evaluate_js = evaluate_js
        self._ready = False
        self._pending: list[str] = []
        self._lock = threading.Lock()

    def on_event(self, event: UiEvent) -> None:
        script = self._to_script(event)
        if script is None:
            return
        with self._lock:
            if not self._ready:
                self._pending.append(script)
                return
            self._run(script)

    def mark_ready(self) -> None:
        """Call when the page has loaded; flushes queued events."""
        with self._lock:
            self._ready = True
            pending, self._pending = self._pending, []
            for script in pending:
                self._run(script)

    @staticmethod
    def _to_script(event: UiEvent) -> str | None:
        if isinstance(event, StateChanged):
            return f"window.fridayUi.setState({json.dumps(event.state.value)})"
        if isinstance(event, MessageAdded):
            return (
                f"window.fridayUi.addMessage({json.dumps(event.role)}, "
                f"{json.dumps(event.text)})"
            )
        logger.warning("unknown UI event %r", event)
        return None

    def _run(self, script: str) -> None:
        try:
            self._evaluate_js(script)
        except Exception:
            logger.exception("could not update the window")
