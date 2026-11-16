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


UiEvent = StateChanged | MessageAdded
Listener = Callable[[UiEvent], None]


class UiEventBus:
    """Thread-safe publish/subscribe. A failing listener never breaks others."""

    def __init__(self) -> None:
        self._listeners: list[Listener] = []
        self._lock = threading.Lock()

    def subscribe(self, listener: Listener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def publish(self, event: UiEvent) -> None:
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                logger.exception("UI listener failed on %r", event)
