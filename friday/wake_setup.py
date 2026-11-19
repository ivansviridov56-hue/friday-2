"""Small pieces for wiring the wake word listener into voice.py.

- env_flag: read an on/off switch from .env ("1", "true", "yes", "on");
- WakeIndicator: window state while the listener waits for the command;
- SerializedTranscriber: one speech model shared by the listener thread and the
  assistant thread, one recognition at a time (not sure the model is safe for
  parallel calls, and the cost of waiting a fraction of a second is nothing).
"""

from __future__ import annotations

import logging
import threading
from typing import Protocol

import numpy as np

from friday.ui_events import State, StateChanged, UiEventBus

log = logging.getLogger(__name__)

_TRUE = frozenset({"1", "true", "yes", "on"})


def env_flag(value: str | None) -> bool:
    """True for "1", "true", "yes", "on" (any case); anything else, including None, is False."""
    return (value or "").strip().lower() in _TRUE


class WakeIndicator:
    """Shows LISTENING while the name was heard and the command is awaited.

    "wake" -> LISTENING, "timeout" -> IDLE. "command" is left to the assistant (it
    publishes THINKING itself) and "cancel" means the assistant or X2 took over the
    window, so the indicator must not touch it.
    """

    def __init__(self, bus: UiEventBus) -> None:
        self._bus = bus

    def on_event(self, name: str) -> None:
        if name == "wake":
            self._bus.publish(StateChanged(State.LISTENING))
        elif name == "timeout":
            self._bus.publish(StateChanged(State.IDLE))


class _Transcriber(Protocol):
    def transcribe(self, audio: np.ndarray) -> str: ...


class SerializedTranscriber:
    def __init__(self, inner: _Transcriber) -> None:
        self._inner = inner
        self._lock = threading.Lock()

    def transcribe(self, audio: np.ndarray) -> str:
        with self._lock:
            return self._inner.transcribe(audio)
