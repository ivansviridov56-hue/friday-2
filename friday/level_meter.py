"""Turns microphone frames into a smooth 0..1 loudness number for the window."""

from __future__ import annotations

import math
import time
from typing import Callable

import numpy as np

DEFAULT_GATE = 0.004  # RMS below this is room noise (same as the wake segmenter)
DEFAULT_FULL = 0.05  # RMS that counts as "full loudness"
DEFAULT_INTERVAL = 0.05  # seconds between emitted values (20 per second)
DEFAULT_ATTACK = 0.7  # how fast the level rises (share of the gap per emit)
DEFAULT_RELEASE = 0.25  # how fast the level falls


class LevelMeter:
    """feed() is cheap and safe for the audio thread: it only does arithmetic.

    It returns a new level at most once per interval, otherwise None. Sending the
    number to the window is the caller's job (not in the audio thread).
    """

    def __init__(
        self,
        *,
        gate: float = DEFAULT_GATE,
        full: float = DEFAULT_FULL,
        interval: float = DEFAULT_INTERVAL,
        attack: float = DEFAULT_ATTACK,
        release: float = DEFAULT_RELEASE,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if gate < 0 or full <= gate:
            raise ValueError("need 0 <= gate < full")
        if interval <= 0:
            raise ValueError("interval must be positive")
        if not (0 < attack <= 1 and 0 < release <= 1):
            raise ValueError("attack and release must be in (0, 1]")
        self._gate = gate
        self._full = full
        self._interval = interval
        self._attack = attack
        self._release = release
        self._clock = clock
        self._level = 0.0
        self._sum_sq = 0.0
        self._count = 0
        self._last_emit = clock()

    def feed(self, frame: np.ndarray) -> float | None:
        if frame.size:
            samples = frame.astype(np.float64, copy=False)
            self._sum_sq += float(np.square(samples).sum())
            self._count += frame.size
        now = self._clock()
        if now - self._last_emit < self._interval or self._count == 0:
            return None
        self._last_emit = now
        rms = math.sqrt(self._sum_sq / self._count)
        self._sum_sq = 0.0
        self._count = 0
        target = (rms - self._gate) / (self._full - self._gate)
        target = min(1.0, max(0.0, target))
        speed = self._attack if target > self._level else self._release
        self._level += (target - self._level) * speed
        return self._level

    def reset(self) -> None:
        """Forget the level (for example when listening ends)."""
        self._level = 0.0
        self._sum_sq = 0.0
        self._count = 0
        self._last_emit = self._clock()
