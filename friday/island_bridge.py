"""Forwards the assistant state, theme and answer text from the UI event bus to the island."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any, Protocol

from friday.island_logic import clip_text
from friday.text_reveal import locate_chunk
from friday.ui_events import (
    MessageAdded,
    SpeechChunkStarted,
    State,
    StateChanged,
    ThemeChanged,
    UiEvent,
    UiEventBus,
)

log = logging.getLogger(__name__)

HIDE_DELAY = 1.5  # seconds between the end of her speech and hiding the text
MAX_REVEAL_CHARS = (
    2500  # a longer answer is shown at once (the island takes about 3000)
)


def _squash(text: str) -> str:
    """Collapse all whitespace, the same way for the answer and for its spoken pieces."""
    return " ".join(text.split())


class StateShower(Protocol):
    def set_state(self, state: str) -> None: ...
    def set_theme(self, theme: str) -> None: ...
    def show_text(self, text: str) -> None: ...
    def clear_text(self) -> None: ...
    def start_reveal(self, text: str) -> None: ...
    def reveal_chunk(self, start: int, end: int, seconds: float) -> None: ...
    def finish_reveal(self) -> None: ...


class IslandBridge:
    def __init__(
        self,
        bus: UiEventBus,
        island: StateShower,
        hide_delay: float = HIDE_DELAY,
        timer_factory: Callable[..., Any] = threading.Timer,
    ) -> None:
        self._bus = bus
        self._island = island
        self._hide_delay = hide_delay
        self._timer_factory = timer_factory
        self._subscribed = False
        self._text_shown = False
        self._timer: Any = None
        self._reveal_text: str | None = (
            None  # the answer being revealed in step with her voice
        )
        self._reveal_pos = 0  # where the next spoken piece may start
        self._lock = threading.Lock()

    def start(self) -> None:
        """Subscribe to the bus; the last known theme and state are delivered at once."""
        if self._subscribed:
            return
        self._subscribed = True
        self._bus.subscribe(self._on_event)

    def close(self) -> None:
        if not self._subscribed:
            return
        self._subscribed = False
        self._bus.unsubscribe(self._on_event)
        with self._lock:
            self._cancel_timer()

    def _on_event(self, event: UiEvent) -> None:
        if isinstance(event, StateChanged):
            self._island.set_state(event.state.value)
            finish = False
            with self._lock:
                if event.state is State.SPEAKING:
                    self._cancel_timer()
                else:
                    finish = self._reveal_text is not None
                    self._reveal_text = None
                    if self._text_shown:
                        self._schedule_hide()
            if finish:
                self._island.finish_reveal()
        elif isinstance(event, ThemeChanged):
            self._island.set_theme(event.name)
        elif isinstance(event, MessageAdded) and event.role == "assistant":
            text = _squash(event.text)
            if not text:
                return
            reveal = event.spoken and len(text) <= MAX_REVEAL_CHARS
            with self._lock:
                self._cancel_timer()
                self._text_shown = True
                self._reveal_text = text if reveal else None
                self._reveal_pos = 0
            if reveal:
                self._island.start_reveal(text)
            else:
                self._island.show_text(clip_text(event.text))
        elif isinstance(event, SpeechChunkStarted):
            with self._lock:
                span = self._locate(event.text)
            if span is not None:
                self._island.reveal_chunk(span[0], span[1], event.seconds)

    def _locate(self, chunk: str) -> tuple[int, int] | None:
        """Where a spoken piece sits in the answer; None if it is not part of it.

        Call with the lock held.
        """
        if self._reveal_text is None:
            return None
        span = locate_chunk(self._reveal_text, _squash(chunk), self._reveal_pos)
        if span is not None:
            self._reveal_pos = span[1]
        return span

    def _schedule_hide(self) -> None:
        self._cancel_timer()
        timer = self._timer_factory(self._hide_delay, self._hide)
        timer.daemon = True
        self._timer = timer
        timer.start()

    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _hide(self) -> None:
        with self._lock:
            if not self._text_shown:
                return
            self._text_shown = False
            self._timer = None
        self._island.clear_text()
