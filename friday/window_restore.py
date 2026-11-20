"""Restore minimized windows of given processes (Windows only).

Live-checked, no unit tests. UI Automation hides minimized windows
(visible_only), so they are found through Win32 by process id instead.
"""

from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

logger = logging.getLogger(__name__)

SW_RESTORE = 9


def restore_minimized(pids: list[int]) -> int:
    """Restore every minimized top-level window of the given processes.

    Returns how many windows were restored.
    """
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]  # Windows only
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]

    wanted = set(pids)
    restored: list[int] = []

    def visit(hwnd, _lparam) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if (
            pid.value in wanted
            and user32.IsWindowVisible(hwnd)
            and user32.IsIconic(hwnd)
        ):
            user32.ShowWindow(hwnd, SW_RESTORE)
            restored.append(hwnd)
        return True

    user32.EnumWindows(enum_proc(visit), 0)
    logger.info(
        "restore: %d process(es), %d minimized window(s) restored",
        len(wanted),
        len(restored),
    )
    return len(restored)
