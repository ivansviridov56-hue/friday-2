"""Tells the window that the wallpaper is about to change.

Windows rewrites the wallpaper file about 1.1 s before it changes the accent colour (and
before the blur snaps), and writes it 2-4 times in a row. The first write is the signal;
the rest of the burst is ignored.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Protocol

log = logging.getLogger(__name__)

POLL_SECONDS = 0.1
MIN_GAP_SECONDS = 2.0


class WallpaperSource(Protocol):
    def stamp(self) -> int | None:
        """Change time of the wallpaper file, None if unknown."""


class WallpaperWatcher:
    """Calls on_change once per wallpaper change."""

    def __init__(
        self,
        source: WallpaperSource,
        on_change: Callable[[], None],
        interval: float = POLL_SECONDS,
        min_gap: float = MIN_GAP_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._source = source
        self._on_change = on_change
        self._interval = interval
        self._min_gap = min_gap
        self._clock = clock
        self._seen = False
        self._last: int | None = None
        self._last_fired: float | None = None
        self._failing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def poll_once(self) -> None:
        try:
            self._poll()
            self._failing = False
        except Exception:
            if not self._failing:
                log.exception("wallpaper watching failed")
            self._failing = True

    def _poll(self) -> None:
        stamp = self._source.stamp()
        if not self._seen:
            # The first reading is only the starting point.
            self._seen = True
            self._last = stamp
            return
        if stamp == self._last:
            return
        self._last = stamp
        now = self._clock()
        if self._last_fired is not None and now - self._last_fired < self._min_gap:
            return
        self._last_fired = now
        self._on_change()

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name="wallpaper-watcher", daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        self.poll_once()
        while not self._stop.wait(self._interval):
            self.poll_once()
