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

SW_MINIMIZE = 6


def restore_minimized(pids: list[int]) -> list[int]:
    """Restore every minimized top-level window of the given processes.

    Returns the handles of the restored windows.
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
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]

    wanted = set(pids)
    restored: list[int] = []
    seen: list[str] = []

    def visit(hwnd, _lparam) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value not in wanted:
            return True
        visible = bool(user32.IsWindowVisible(hwnd))
        iconic = bool(user32.IsIconic(hwnd))
        buf = ctypes.create_unicode_buffer(8)
        user32.GetWindowTextW(hwnd, buf, 8)
        if visible or buf.value:
            seen.append(f"visible={visible} iconic={iconic} titled={bool(buf.value)}")
        if visible and iconic:
            user32.ShowWindow(hwnd, SW_RESTORE)
            restored.append(hwnd)
        return True

    user32.EnumWindows(enum_proc(visit), 0)

    if not restored:
        logger.info("restore: windows seen: %s", seen or "none")

    logger.info(
        "restore: %d process(es), %d minimized window(s) restored",
        len(wanted),
        len(restored),
    )
    return restored


def minimize_windows(hwnds: list[int]) -> None:
    """Minimize the given windows again (the ones restore_minimized returned)."""
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]  # Windows only
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    for hwnd in hwnds:
        user32.ShowWindow(hwnd, SW_MINIMIZE)
    logger.info("minimized %d window(s) back", len(hwnds))
