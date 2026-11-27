"""Fade of the whole window in and out. No Windows calls here.

show() and hide() return at once; the animation runs in a worker thread. This matters
because the closing event calls hide() while the interface thread waits for it, and
setting the opacity needs that same thread. So no caller of hide() or show() ever
waits for a running animation. A newer request stops the older one, which continues
from the opacity reached so far.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

log = logging.getLogger(__name__)

FADE_SECONDS = 0.35  # a full fade; checked live
FRAME = 1 / 60


def _spawn_thread(job: Callable[[], None]) -> None:
    threading.Thread(target=job, daemon=True, name="window-fade").start()


class WindowFade:
    def __init__(
        self,
        set_opacity: Callable[[float], object],
        show: Callable[[], object],
        hide: Callable[[], object],
        spawn: Callable[[Callable[[], None]], object] = _spawn_thread,
        clock: Callable[[], float] = time.perf_counter,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        self._set_opacity = set_opacity
        self._show = show
        self._hide = hide
        self._spawn = spawn
        self._clock = clock
        self._sleep = sleep
        self._state = threading.Lock()  # never held while calling the window
        self._running = threading.Lock()  # one animation at a time; workers only
        self._request = 0
        self._level = 1.0
        self._hide_failed = False

    def show(self) -> None:
        """Show the window and fade it in."""
        request = self._new_request()
        self._spawn(lambda: self._show_job(request))

    def hide(self) -> None:
        """Fade the window out and hide it. Raises if hiding has failed before."""
        if self._hide_failed:
            # Lets the caller close the window rather than trap the user.
            raise RuntimeError("the window could not be hidden")
        request = self._new_request()
        self._spawn(lambda: self._hide_job(request))

    def appear(self, uncloak: Callable[[], bool]) -> bool:
        """The first appearance: uncloak a transparent window, then fade it in.

        Never call this from the interface thread. True when the window was uncloaked.
        """
        request = self._new_request()
        with self._running:
            self._apply(0.0)
            if not uncloak():
                self._apply(1.0)
                return False
        self._spawn(lambda: self._appear_job(request))
        return True

    def close(self) -> None:
        """The window is going away: stop any animation."""
        self._new_request()

    def _new_request(self) -> int:
        with self._state:
            self._request += 1
            return self._request

    def _is_current(self, request: int) -> bool:
        with self._state:
            return request == self._request

    def _show_job(self, request: int) -> None:
        with self._running:
            if not self._is_current(request):
                return
            try:
                self._show()
            except Exception:
                log.exception("could not show the window")
            self._fade(1.0, request)

    def _appear_job(self, request: int) -> None:
        with self._running:
            if self._is_current(request):
                self._fade(1.0, request)

    def _hide_job(self, request: int) -> None:
        with self._running:
            if not self._is_current(request):
                return
            if not self._fade(0.0, request):
                return
            try:
                self._hide()
            except Exception:
                log.exception("could not hide the window")
                self._hide_failed = True
                self._apply(1.0)  # never leave an invisible window on screen

    def _fade(self, target: float, request: int) -> bool:
        """Animate to the target; False if a newer request took over."""
        start = self._level
        duration = FADE_SECONDS * abs(target - start)
        began = self._clock()
        while self._is_current(request):
            passed = self._clock() - began
            part = min(passed / duration, 1.0) if duration > 0 else 1.0
            eased = 1 - (1 - part) ** 3
            value = target if part >= 1.0 else start + (target - start) * eased
            if not self._apply(value):
                self._apply(target)  # no animation, but the right end state
                return True
            if part >= 1.0:
                return True
            self._sleep(FRAME)
        return False

    def _apply(self, value: float) -> bool:
        try:
            self._set_opacity(value)
        except Exception:
            log.exception("could not set the window opacity")
            return False
        self._level = value
        return True
