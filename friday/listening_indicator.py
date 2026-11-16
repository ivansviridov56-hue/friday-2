"""Shows the LISTENING state around push-to-talk presses.

Only shows it when the assistant is free, and returns to IDLE when a press
produced no audio turn (too short, or dropped because the assistant is busy).
"""

from __future__ import annotations

import logging
from typing import Callable

from friday.ui_events import State, StateChanged, UiEventBus

logger = logging.getLogger(__name__)


class ListeningIndicator:
    def __init__(self, bus: UiEventBus, is_busy: Callable[[], bool]) -> None:
        self._bus = bus
        self._is_busy = is_busy
        self._showing = False

    def on_press(self) -> None:
        if self._is_busy():
            return
        self._showing = True
        self._bus.publish(StateChanged(State.LISTENING))

    def on_audio_submitted(self, accepted: bool) -> None:
        """Call with the result of TurnRunner.submit for a finished press."""
        if self._showing and not accepted:
            self._bus.publish(StateChanged(State.IDLE))
        self._showing = False

    def on_release(self) -> None:
        """Call after PushToTalk.release returns."""
        if self._showing:
            # release produced no submit: the press was too short
            self._bus.publish(StateChanged(State.IDLE))
            self._showing = False
