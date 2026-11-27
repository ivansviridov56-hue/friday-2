"""Window calls for the minimize animation. Live-checked, no unit tests.

A private WinDLL is used on purpose: argument types set on the shared
ctypes.windll.user32 would break pywebview's own SetWindowPos calls (window drag).
"""

from __future__ import annotations

import ctypes
import logging
from collections.abc import Callable
from ctypes import wintypes
from typing import Any

log = logging.getLogger(__name__)

GWL_STYLE = -16
WM_NCDESTROY = 0x0082
WM_STYLECHANGING = 0x007C
WM_SYSCOMMAND = 0x0112
SC_MINIMIZE = 0xF020
WS_MINIMIZEBOX = 0x00020000  # lets a click on the taskbar icon minimize the window
SWP_MOVE_ONLY = 0x0001 | 0x0004 | 0x0010  # keep the size, the order and the focus
SUBCLASS_ID = 1


class _StyleChange(ctypes.Structure):
    _fields_ = [("old", wintypes.DWORD), ("new", wintypes.DWORD)]


class WindowMotion:
    """Position and state of the window, and the taskbar's request to minimize it."""

    def __init__(self, window: object) -> None:
        self._window: Any = window
        self._user32: Any = None
        self._comctl: Any = None
        self._hwnd: ctypes.c_void_p | None = None
        self._proc: Any = None  # must live as long as the window
        self.attached = False

    def attach(self, on_minimize: Callable[[], object]) -> bool:
        """Call on the interface thread (before_show). False: keep the plain minimize."""
        try:
            self._load()
            self._hwnd = ctypes.c_void_p(self._window.native.Handle.ToInt64())
            self._proc = self._make_proc(on_minimize)
            if not self._comctl.SetWindowSubclass(
                self._hwnd, self._proc, SUBCLASS_ID, 0
            ):
                log.warning("could not watch the window messages")
                return False
            style = self._user32.GetWindowLongPtrW(self._hwnd, GWL_STYLE)
            self._user32.SetWindowLongPtrW(
                self._hwnd, GWL_STYLE, style | WS_MINIMIZEBOX
            )
        except Exception:
            log.exception("minimize animation is not available")
            return False
        self.attached = True
        return True

    def position(self) -> tuple[int, int]:
        rect = wintypes.RECT()
        if not self._user32.GetWindowRect(self._hwnd, ctypes.byref(rect)):
            raise OSError("GetWindowRect failed")
        return rect.left, rect.top

    def move(self, x: int, y: int) -> None:
        self._user32.SetWindowPos(self._hwnd, None, x, y, 0, 0, SWP_MOVE_ONLY)

    def minimize(self) -> None:
        self._window.minimize()

    def restore(self) -> None:
        self._window.restore()

    def is_minimized(self) -> bool:
        return self._hwnd is not None and bool(self._user32.IsIconic(self._hwnd))

    def _load(self) -> None:
        handle = ctypes.c_void_p
        user32 = ctypes.WinDLL("user32")
        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.GetWindowLongPtrW.argtypes = [handle, ctypes.c_int]
        user32.SetWindowLongPtrW.argtypes = [handle, ctypes.c_int, ctypes.c_ssize_t]
        user32.SetWindowPos.argtypes = (
            [handle, handle] + [ctypes.c_int] * 4 + [ctypes.c_uint]
        )
        user32.GetWindowRect.argtypes = [handle, ctypes.POINTER(wintypes.RECT)]
        user32.IsIconic.argtypes = [handle]
        self._user32 = user32
        self._comctl = ctypes.WinDLL("comctl32")

    def _make_proc(self, on_minimize: Callable[[], object]) -> Any:
        handle = ctypes.c_void_p
        proc_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            handle,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
            ctypes.c_size_t,
            ctypes.c_size_t,
        )
        comctl = self._comctl
        comctl.DefSubclassProc.restype = ctypes.c_ssize_t
        comctl.DefSubclassProc.argtypes = [
            handle,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        comctl.SetWindowSubclass.argtypes = [
            handle,
            proc_type,
            ctypes.c_size_t,
            ctypes.c_size_t,
        ]
        comctl.RemoveWindowSubclass.argtypes = [handle, proc_type, ctypes.c_size_t]

        def window_proc(hwnd, message, wparam, lparam, _id, _data):
            try:
                if message == WM_SYSCOMMAND and (wparam & 0xFFF0) == SC_MINIMIZE:
                    on_minimize()  # returns at once; minimizes after the animation
                    return 0
                if (
                    message == WM_STYLECHANGING
                    and ctypes.c_int32(wparam & 0xFFFFFFFF).value == GWL_STYLE
                ):
                    # WinForms may rebuild the style (opacity changes); keep our bit.
                    _StyleChange.from_address(lparam).new |= WS_MINIMIZEBOX
                if message == WM_NCDESTROY:
                    comctl.RemoveWindowSubclass(hwnd, self._proc, SUBCLASS_ID)
            except Exception:
                log.exception("window message handling failed")
            return comctl.DefSubclassProc(hwnd, message, wparam, lparam)

        return proc_type(window_proc)
