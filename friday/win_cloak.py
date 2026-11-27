"""DWM cloaking: the window exists and renders but is not on screen. Live-checked, no unit tests."""

from __future__ import annotations

import ctypes
import logging

log = logging.getLogger(__name__)

DWMWA_CLOAK = 13


class WindowCloak:
    def __init__(self, window: object) -> None:
        self._window = window
        self._hwnd: int | None = None

    def cloak(self) -> bool:
        """Call in the before_show event: the handle exists, the window is not shown yet."""
        try:
            self._hwnd = self._window.native.Handle.ToInt64()  # type: ignore[attr-defined]
        except Exception:
            log.exception("could not get the window handle")
            return False
        return self._set(True)

    def uncloak(self) -> bool:
        return self._set(False)

    def _set(self, cloaked: bool) -> bool:
        if self._hwnd is None:
            return False
        try:
            value = ctypes.c_int(1 if cloaked else 0)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(self._hwnd),
                DWMWA_CLOAK,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            log.exception("cloak call failed")
            return False
        if result != 0:
            log.warning("cloak call returned %s", result)
        return result == 0
