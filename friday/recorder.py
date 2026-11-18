"""Microphone capture (mono float32, 16 kHz).

The input stream stays open while the assistant runs, so recording starts
instantly. Audio is kept only between start() and stop().
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

import numpy as np

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000

StreamFactory = Callable[[int, int, str, Callable[..., None]], Any]


def _default_stream_factory(
    samplerate: int, channels: int, dtype: str, callback: Callable[..., None]
) -> Any:
    import sounddevice as sd

    return sd.InputStream(
        samplerate=samplerate, channels=channels, dtype=dtype, callback=callback
    )


class Recorder:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        stream_factory: StreamFactory | None = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._factory = stream_factory or _default_stream_factory
        self._stream: Any = None
        self._recording = False
        self._chunks: list[np.ndarray] = []
        self._listeners: list[Callable[[np.ndarray], object]] = []
        self._lock = threading.RLock()

    @property
    def is_open(self) -> bool:
        return self._stream is not None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def _callback(
        self, indata: np.ndarray, frames: int, time_info: Any, status: Any
    ) -> None:
        if status:
            log.warning("audio status: %s", status)
        mono = indata[:, 0].copy()
        with self._lock:
            if self._recording:
                self._chunks.append(mono)
            listeners = tuple(self._listeners)
        for listener in listeners:  # outside the lock; must be fast, must not modify
            try:
                listener(mono)
            except Exception:  # a broken listener must not kill the audio stream
                log.exception("audio listener failed")

    def add_listener(self, listener: Callable[[np.ndarray], object]) -> None:
        """Get every audio frame (mono float32), recording or not.

        Called from the audio thread: put the frame in a queue and return at once.
        Adding the same listener twice has no effect.
        """
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[np.ndarray], object]) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def open(self) -> None:
        """Open the microphone stream (idempotent)."""
        with self._lock:
            if self._stream is not None:
                return
            stream = self._factory(self._sample_rate, 1, "float32", self._callback)
            stream.start()
            self._stream = stream
            log.info("microphone stream opened")

    def close(self) -> None:
        with self._lock:
            self._recording = False
            self._chunks = []
            stream, self._stream = self._stream, None
        if stream is not None:  # outside the lock: stop() waits for the callback
            stream.stop()
            stream.close()
            log.info("microphone stream closed")

    def start(self) -> None:
        with self._lock:
            if self._recording:
                return
            self.open()
            self._chunks = []
            self._recording = True
        log.debug("recording started")

    def stop(self) -> np.ndarray:
        with self._lock:
            if not self._recording:
                return np.zeros(0, dtype=np.float32)
            self._recording = False
            chunks, self._chunks = self._chunks, []
        log.debug("recording stopped, %d chunks", len(chunks))
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks)
