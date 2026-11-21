"""Window commands (minimize, close, resize) that the page can trigger.

The window does not exist yet when the API is created, so the callbacks are bound
later by friday/window.py and cleared when the window closes. Sizes are clamped
to the limits given here.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

log = logging.getLogger(__name__)

Action = Callable[[], object]
ResizeAction = Callable[[int, int], object]

MIN_SIZE = (320, 420)
MAX_SIZE = (4000, 3000)


class WindowControls:
    def __init__(
        self,
        min_size: tuple[int, int] = MIN_SIZE,
        max_size: tuple[int, int] = MAX_SIZE,
    ) -> None:
        if (
            min_size[0] < 1
            or min_size[1] < 1
            or max_size[0] < min_size[0]
            or max_size[1] < min_size[1]
        ):
            raise ValueError("bad window size limits")
        self._min_size = min_size
        self._max_size = max_size
        self._minimize: Action | None = None
        self._close: Action | None = None
        self._resize: ResizeAction | None = None
        self._lock = threading.Lock()

    def bind(
        self,
        minimize: Action,
        close: Action,
        resize: ResizeAction | None = None,
    ) -> None:
        with self._lock:
            self._minimize = minimize
            self._close = close
            self._resize = resize

    def unbind(self) -> None:
        with self._lock:
            self._minimize = None
            self._close = None
            self._resize = None

    def minimize(self) -> bool:
        with self._lock:
            action = self._minimize
        return self._run("minimize", action)

    def close(self) -> bool:
        with self._lock:
            action = self._close
        return self._run("close", action)

    def resize(self, width: float, height: float) -> bool:
        with self._lock:
            action = self._resize
        if action is None:
            log.info("window resize ignored: the window is not ready")
            return False
        new_width = int(min(max(width, self._min_size[0]), self._max_size[0]))
        new_height = int(min(max(height, self._min_size[1]), self._max_size[1]))
        try:
            action(new_width, new_height)
        except Exception:
            log.exception("window resize failed")
            return False
        return True

    @staticmethod
    def _run(name: str, action: Action | None) -> bool:
        if action is None:
            log.info("window %s ignored: the window is not ready", name)
            return False
        try:
            action()
        except Exception:
            log.exception("window %s failed", name)
            return False
        return True
