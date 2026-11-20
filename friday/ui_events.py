"""UI-facing events: assistant state and chat messages.

Independent of any window toolkit, so it can be tested without a GUI.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Literal

logger = logging.getLogger(__name__)


class State(str, Enum):
    LOADING = "loading"
    ERROR = "error"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


@dataclass(frozen=True)
class StateChanged:
    state: State


@dataclass(frozen=True)
class MessageAdded:
    role: Literal["user", "assistant"]
    text: str


@dataclass(frozen=True)
class LevelChanged:
    """Microphone loudness 0..1 for the window; not remembered by the bus."""

    level: float


UiEvent = StateChanged | MessageAdded | LevelChanged
Listener = Callable[[UiEvent], None]


class UiEventBus:
    """Thread-safe publish/subscribe. A failing listener never breaks others.

    Remembers the last state: a listener that subscribes late gets it at once,
    so it never misses a state published before it joined.
    """

    def __init__(self) -> None:
        self._listeners: list[Listener] = []
        self._last_state: StateChanged | None = None
        self._lock = threading.Lock()

    def subscribe(self, listener: Listener) -> None:
        with self._lock:
            self._listeners.append(listener)
            last = self._last_state
        if last is not None:
            self._deliver(listener, last)

    def unsubscribe(self, listener: Listener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def publish(self, event: UiEvent) -> None:
        with self._lock:
            if isinstance(event, StateChanged):
                self._last_state = event
            listeners = list(self._listeners)
        for listener in listeners:
            self._deliver(listener, event)

    @staticmethod
    def _deliver(listener: Listener, event: UiEvent) -> None:
        try:
            listener(event)
        except Exception:
            logger.exception("UI listener failed on %r", event)
