"""Push-to-talk logic: record while the trigger is held, deliver audio on release."""

from __future__ import annotations

import logging
import time
from typing import Callable, Protocol

import numpy as np

log = logging.getLogger(__name__)


class AudioRecorder(Protocol):
    def start(self) -> None: ...
    def stop(self) -> np.ndarray: ...


class PushToTalk:
    def __init__(
        self,
        recorder: AudioRecorder,
        on_audio: Callable[[np.ndarray], object],
        min_duration: float = 0.3,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._recorder = recorder
        self._on_audio = on_audio
        self._min_duration = min_duration
        self._clock = clock
        self._pressed_at: float | None = None

    def press(self) -> None:
        if self._pressed_at is not None:
            return
        self._pressed_at = self._clock()
        self._recorder.start()

    def release(self) -> None:
        if self._pressed_at is None:
            return
        held = self._clock() - self._pressed_at
        self._pressed_at = None
        audio = self._recorder.stop()
        if held < self._min_duration:
            log.info("press too short (%.2f s), discarded", held)
            return
        self._on_audio(audio)
