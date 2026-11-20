"""Sends the microphone loudness to the window while the assistant is listening."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Callable, Protocol

import numpy as np

from friday.level_meter import LevelMeter
from friday.ui_events import LevelChanged, State, StateChanged, UiEvent, UiEventBus

log = logging.getLogger(__name__)

QUEUE_SIZE = 200  # about 6 s of frames; older audio is useless for the window


class AudioSource(Protocol):
    def add_listener(self, listener: Callable[[np.ndarray], object]) -> None: ...

    def remove_listener(self, listener: Callable[[np.ndarray], object]) -> None: ...


class LevelPublisher:
    """on_frame() runs in the audio thread and only queues; a worker does the rest."""

    def __init__(
        self,
        bus: UiEventBus,
        source: AudioSource,
        meter: LevelMeter | None = None,
    ) -> None:
        self._bus = bus
        self._source = source
        self._meter = meter if meter is not None else LevelMeter()
        self._listening = False
        self._sending = False
        self._frames: queue.Queue[np.ndarray] = queue.Queue(maxsize=QUEUE_SIZE)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        bus.subscribe(self._on_event)

    def _on_event(self, event: UiEvent) -> None:
        if isinstance(event, StateChanged):
            self._listening = event.state == State.LISTENING

    def on_frame(self, frame: np.ndarray) -> None:
        try:
            self._frames.put_nowait(frame)
        except queue.Full:
            pass

    def handle_frame(self, frame: np.ndarray) -> None:
        if not self._listening:
            if self._sending:
                self._sending = False
                self._meter.reset()
                self._bus.publish(LevelChanged(0.0))
            return
        level = self._meter.feed(frame)
        if level is not None:
            self._sending = True
            self._bus.publish(LevelChanged(level))

    def start(self) -> None:
        self._source.add_listener(self.on_frame)
        self._thread = threading.Thread(
            target=self._run, name="level-publisher", daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        self._source.remove_listener(self.on_frame)
        self._stop.set()
        self._bus.unsubscribe(self._on_event)
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._frames.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.handle_frame(frame)
            except Exception:
                log.exception("level publisher failed")
