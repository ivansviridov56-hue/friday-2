"""Hide / show / quit of the window, so the app can live in the tray.

Closing the window (the X button, Alt+F4) only hides it. The app really exits only
after quit() (the tray menu). The callbacks are bound by friday/window.py once the
window exists and cleared when it is gone.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

log = logging.getLogger(__name__)

Action = Callable[[], object]


class WindowLifecycle:
    def __init__(self) -> None:
        self._show: Action | None = None
        self._hide: Action | None = None
        self._destroy: Action | None = None
        self._quitting = False
        self._lock = threading.Lock()

    def bind(self, show: Action, hide: Action, destroy: Action) -> None:
        with self._lock:
            self._show = show
            self._hide = hide
            self._destroy = destroy

    def unbind(self) -> None:
        with self._lock:
            self._show = None
            self._hide = None
            self._destroy = None

    def show(self) -> bool:
        with self._lock:
            action = self._show
        return self._run("show", action)

    def hide(self) -> bool:
        with self._lock:
            action = self._hide
        return self._run("hide", action)

    def on_closing(self) -> bool:
        """Handler of the window's closing event: True lets it close, False cancels."""
        with self._lock:
            if self._quitting:
                return True
        # If the window cannot be hidden, let it close rather than trap the user.
        return not self.hide()

    def quit(self) -> bool:
        with self._lock:
            destroy = self._destroy
            if destroy is None:
                log.info("quit ignored: the window is not ready")
                return False
            self._quitting = True
        try:
            destroy()
        except Exception:
            log.exception("window quit failed")
            with self._lock:
                self._quitting = False
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
