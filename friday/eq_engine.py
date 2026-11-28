"""Turns blocks of loudspeaker sound into equalizer levels. Needs numpy (local only)."""

from __future__ import annotations

import threading

import numpy as np

from friday.eq_bands import EqSmoother, band_edges, band_levels
from friday.eq_protocol import EQ_BANDS
from friday.spectrum import hann_window, magnitudes, to_mono

BIG_WINDOW = 8192  # samples; a finer picture of the bass at high sample rates
SMALL_WINDOW = 4096
BIG_WINDOW_FROM_RATE = 64000
TILT = 0.7  # music has less energy in the highs: this lifts the bars of high bands
COMPRESS = 0.5  # below 1: shrinks the gap between loud and quiet bands
GATE = 2e-4  # magnitude below this in every band counts as silence (a noise gate)


def window_size(sample_rate: int) -> int:
    """Length of the analysed block; the bass needs a longer one when the rate is high."""
    return BIG_WINDOW if sample_rate >= BIG_WINDOW_FROM_RATE else SMALL_WINDOW


class EqEngine:
    """feed() takes raw 16-bit blocks from any thread; levels() gives the bars 0..1."""

    def __init__(self, sample_rate: int, channels: int, bands: int = EQ_BANDS) -> None:
        self._channels = channels
        self._size = window_size(sample_rate)
        self._window = hann_window(self._size)
        self._edges = band_edges(bands, self._size, sample_rate)
        self._weights = [((lo + hi) / 2) ** TILT for lo, hi in self._edges]
        self._buffer = np.zeros(self._size, dtype=np.float32)
        self._smoother = EqSmoother(bands)
        self._bands = bands
        self._lock = threading.Lock()

    @property
    def fft_size(self) -> int:
        return self._size

    def feed(self, raw: bytes) -> None:
        mono = to_mono(raw, self._channels)
        if len(mono) == 0:
            return
        with self._lock:
            if len(mono) >= self._size:
                self._buffer = mono[-self._size :].copy()
            else:
                self._buffer = np.concatenate((self._buffer[len(mono) :], mono))

    def levels(self, dt: float) -> list[float]:
        """Bar heights 0..1 for the latest sound; call about 30 times a second."""
        with self._lock:
            block = self._buffer.copy()
        raw = band_levels(magnitudes(block, self._window), self._edges)
        if max(raw) < GATE:
            shaped = [0.0] * self._bands
        else:
            shaped = [(v * w) ** COMPRESS for v, w in zip(raw, self._weights)]
        return self._smoother.update(shaped, dt)
