"""Equalizer bands from a sound spectrum. Pure logic: no numpy, no audio, no Qt."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # only for type hints; this module never imports numpy at run time
    import numpy as np


def band_edges(
    bands: int,
    fft_size: int,
    sample_rate: int,
    f_min: float = 50.0,
    f_max: float = 12000.0,
) -> list[tuple[int, int]]:
    """Log-spaced bands as (first bin, end bin) pairs; the end bin is not included."""
    if bands < 1:
        raise ValueError("bands must be at least 1")
    if f_min <= 0 or f_max <= f_min:
        raise ValueError("need 0 < f_min < f_max")
    if f_max > sample_rate / 2:
        raise ValueError("f_max must not be above half the sample rate")

    def index(freq: float) -> int:
        return round(freq * fft_size / sample_rate)

    ratio = f_max / f_min
    points = [index(f_min * ratio ** (i / bands)) for i in range(bands + 1)]
    return [(points[i], max(points[i] + 1, points[i + 1])) for i in range(bands)]


def band_levels(
    magnitudes: Sequence[float] | np.ndarray, edges: Sequence[tuple[int, int]]
) -> list[float]:
    """Mean magnitude inside every band; a band outside the spectrum is 0."""
    levels = []
    for lo, hi in edges:
        chunk = magnitudes[lo:hi]
        count = len(chunk)
        levels.append(float(sum(chunk)) / count if count else 0.0)
    return levels


class EqSmoother:
    """Levels of bands -> bar heights 0..1: auto gain, fast attack, slow release."""

    def __init__(
        self,
        bands: int,
        attack: float = 30.0,  # 1/s, how fast a bar rises
        release: float = 6.0,  # 1/s, how fast a bar falls
        peak_decay: float = 0.5,  # 1/s, how fast the remembered loudest level fades
        silence: float = 1e-4,  # below this the input counts as silence
    ) -> None:
        if bands < 1:
            raise ValueError("bands must be at least 1")
        self._bands = bands
        self._attack = attack
        self._release = release
        self._peak_decay = peak_decay
        self._silence = silence
        self._values = [0.0] * bands
        self._peak = 0.0

    @property
    def values(self) -> list[float]:
        return list(self._values)

    def update(self, levels: Sequence[float], dt: float) -> list[float]:
        if len(levels) != self._bands:
            raise ValueError(f"expected {self._bands} levels, got {len(levels)}")
        if dt <= 0:
            return self.values
        top = max(levels)
        self._peak *= math.exp(-self._peak_decay * dt)
        if top >= self._silence:
            self._peak = max(self._peak, top)
            targets = [min(1.0, max(0.0, level) / self._peak) for level in levels]
        else:
            targets = [0.0] * self._bands
        for i, target in enumerate(targets):
            rate = self._attack if target > self._values[i] else self._release
            self._values[i] += (target - self._values[i]) * (1 - math.exp(-rate * dt))
        return self.values
