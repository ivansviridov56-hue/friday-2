"""Spectrum of a block of loudspeaker sound. Needs numpy (local requirements only)."""

from __future__ import annotations

import numpy as np


def to_mono(raw: bytes, channels: int) -> np.ndarray:
    """Interleaved 16-bit PCM bytes -> mono float samples in -1..1."""
    if channels < 1:
        raise ValueError("channels must be at least 1")
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    usable = len(data) - len(data) % channels
    return data[:usable].reshape(-1, channels).mean(axis=1)


def hann_window(size: int) -> np.ndarray:
    """Smooth window: without it the edges of a block smear the spectrum."""
    return np.hanning(size).astype(np.float32)


def magnitudes(samples: np.ndarray, window: np.ndarray) -> np.ndarray:
    """Magnitude of every frequency bin (size // 2 + 1 values)."""
    if len(samples) != len(window):
        raise ValueError("the block and the window must have the same length")
    spectrum = np.fft.rfft(samples * window)
    return (np.abs(spectrum) / (len(samples) / 2)).astype(np.float32)
