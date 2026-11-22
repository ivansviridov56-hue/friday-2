"""Bridge: turns UI events into JavaScript calls for the window.

Events that arrive before the page has loaded are queued and flushed in order.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Callable

from friday.ui_events import (
    CirclesStyleChanged,
    CoverChanged,
    LevelChanged,
    MessageAdded,
    StateChanged,
    ThemeChanged,
    UiEvent,
)

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
                if not isinstance(event, LevelChanged):
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
        if isinstance(event, LevelChanged):
            level = min(1.0, max(0.0, event.level))
            return f"window.fridayUi.setLevel({level:.3f})"
        if isinstance(event, CoverChanged):
            return f"window.fridayUi.setCover({json.dumps(event.image)})"
        if isinstance(event, CirclesStyleChanged):
            return f"window.fridayUi.setCirclesStyle({json.dumps(event.name)})"
        if isinstance(event, ThemeChanged):
            return f"window.fridayUi.setTheme({json.dumps(event.name)})"
        logger.warning("unknown UI event %r", event)
        return None

    def _run(self, script: str) -> None:
        try:
            self._evaluate_js(script)
        except Exception:
            logger.exception("could not update the window")
