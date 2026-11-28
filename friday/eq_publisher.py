"""Feeds the island's equalizer with the real sound, only while Yandex Music plays."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import Protocol

log = logging.getLogger(__name__)

POLL_SECONDS = 0.5  # how often to ask whether Music plays
TICK_SECONDS = 1 / 30  # how often the levels go to the island
RETRY_SECONDS = 5.0  # pause after the sound capture failed to start
MAX_DT = 0.1  # a longer pause between two levels counts as this long


class Capture(Protocol):
    rate: int
    channels: int

    def open(self) -> bool: ...
    def start(self, on_block: Callable[[bytes], None]) -> bool: ...
    def close(self) -> None: ...


class Engine(Protocol):
    def feed(self, raw: bytes) -> None: ...
    def levels(self, dt: float) -> list[float]: ...


class EqPublisher:
    """While Music plays: capture the speakers and send the bars to the island.

    When Music pauses or closes, the capture is closed and the sending stops; the island then
    goes back to its usual wave by itself.
    """

    def __init__(
        self,
        is_playing: Callable[[], bool],
        make_capture: Callable[[], Capture],
        make_engine: Callable[[int, int], Engine],
        sink: Callable[[list[float]], None],
        poll_seconds: float = POLL_SECONDS,
        tick_seconds: float = TICK_SECONDS,
        retry_seconds: float = RETRY_SECONDS,
    ) -> None:
        self._is_playing = is_playing
        self._make_capture = make_capture
        self._make_engine = make_engine
        self._sink = sink
        self._poll = poll_seconds
        self._tick = tick_seconds
        self._retry = retry_seconds
        self._capture: Capture | None = None
        self._engine: Engine | None = None
        self._last_poll: float | None = None
        self._last_tick: float | None = None
        self._retry_at = 0.0
        self._poll_failing = False
        self._sink_failing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def step(self, now: float) -> None:
        """One round: maybe ask the player, then send one set of bars. `now` is in seconds."""
        if self._last_poll is None or now - self._last_poll >= self._poll:
            self._last_poll = now
            self._apply(self._playing_now(), now)
        if self._engine is None:
            return
        if self._last_tick is None:
            dt = self._tick
        else:
            dt = min(max(now - self._last_tick, 0.0), MAX_DT)
        self._last_tick = now
        try:
            self._sink(self._engine.levels(dt))
            self._sink_failing = False
        except Exception:
            if not self._sink_failing:
                log.exception("equalizer: could not send the levels")
            self._sink_failing = True

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name="eq-publisher", daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        self._end()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.step(time.monotonic())
            self._stop.wait(self._tick)

    def _playing_now(self) -> bool:
        try:
            playing = bool(self._is_playing())
            self._poll_failing = False
            return playing
        except Exception:
            if not self._poll_failing:
                log.exception("equalizer: could not ask whether Music plays")
            self._poll_failing = True
            return False

    def _apply(self, playing: bool, now: float) -> None:
        if playing and self._capture is None:
            if now >= self._retry_at:
                self._begin(now)
        elif not playing and self._capture is not None:
            self._end()

    def _begin(self, now: float) -> None:
        capture: Capture | None = None
        try:
            capture = self._make_capture()
            if not capture.open():
                raise RuntimeError("no loopback device")
            engine = self._make_engine(capture.rate, capture.channels)
            if not capture.start(engine.feed):
                raise RuntimeError("the capture did not start")
        except Exception as error:
            log.warning("equalizer: the sound capture is not available (%s)", error)
            self._retry_at = now + self._retry
            if capture is not None:
                self._close_quietly(capture)
            return
        self._capture, self._engine, self._last_tick = capture, engine, None

    def _end(self) -> None:
        capture, self._capture = self._capture, None
        self._engine = None
        self._last_tick = None
        if capture is not None:
            self._close_quietly(capture)

    @staticmethod
    def _close_quietly(capture: Capture) -> None:
        try:
            capture.close()
        except Exception:
            log.debug("equalizer: closing the capture failed", exc_info=True)
