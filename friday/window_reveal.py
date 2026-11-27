"""Decides when the cloaked window is shown at start. No Windows calls here.

The window is revealed once: a short moment after it is ready, at once on request
(the tray "open"), or by a safety timeout if "ready" never comes.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Protocol

log = logging.getLogger(__name__)

# Lets the 0.5 s page fade-in finish while the window is still cloaked.
SETTLE_DELAY = 0.6
# The page has its own 3 s safety net for the theme, so this must be longer.
TIMEOUT = 8.0


class Timer(Protocol):
    daemon: bool

    def start(self) -> None: ...

    def cancel(self) -> None: ...


TimerFactory = Callable[[float, Callable[[], object]], Timer]


class WindowReveal:
    def __init__(
        self,
        uncloak: Callable[[], bool],
        timer: TimerFactory = threading.Timer,
    ) -> None:
        self._uncloak = uncloak
        self._timer_factory = timer
        self._timers: list[Timer] = []
        self._lock = threading.Lock()
        self._armed = False
        self._ready = False
        self._settling = False
        self._done = False

    def arm(self, cloaked: bool) -> None:
        """Call right after the attempt to cloak the window, with its result."""
        with self._lock:
            if self._done:
                return
            if not cloaked:
                self._done = True  # the window is visible anyway
                return
            self._armed = True
            self._start_timer(TIMEOUT)
            if self._ready:
                self._settle()

    def ready(self) -> None:
        """The page, the theme and the backdrop are in place."""
        with self._lock:
            self._ready = True
            if self._armed and not self._done:
                self._settle()

    def reveal(self) -> bool:
        """Show the window now. True only for the call that really revealed it."""
        with self._lock:
            if not self._armed or self._done:
                return False
            try:
                ok = self._uncloak()
            except Exception:
                log.exception("could not reveal the window")
                return False
            if not ok:
                log.warning("could not reveal the window")
                return False
            self._done = True
            self._cancel_timers()
            return True

    def close(self) -> None:
        """The window is gone: stop the timers."""
        with self._lock:
            self._done = True
            self._cancel_timers()

    def _settle(self) -> None:  # the caller holds the lock
        if not self._settling:
            self._settling = True
            self._start_timer(SETTLE_DELAY)

    def _start_timer(self, delay: float) -> None:  # the caller holds the lock
        timer = self._timer_factory(delay, self.reveal)
        timer.daemon = True
        self._timers.append(timer)
        timer.start()

    def _cancel_timers(self) -> None:  # the caller holds the lock
        for timer in self._timers:
            timer.cancel()
        self._timers.clear()
