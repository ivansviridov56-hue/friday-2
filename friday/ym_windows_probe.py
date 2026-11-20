"""Diagnostic: list top-level windows of the Yandex Music processes.

Run it while Music is in the state you want to inspect (minimized, closed to tray...).
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from friday.ym_ui import _pids

DWMWA_CLOAKED = 14

user32 = ctypes.windll.user32  # type: ignore[attr-defined]  # Windows only
dwmapi = ctypes.windll.dwmapi  # type: ignore[attr-defined]
ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [ENUM_PROC, wintypes.LPARAM]
user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]


def main() -> None:
    wanted = set(_pids())
    print(f"processes: {sorted(wanted)}")

    def visit(hwnd, _lparam) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in wanted:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            cloaked = wintypes.DWORD()
            dwmapi.DwmGetWindowAttribute(
                wintypes.HWND(hwnd), DWMWA_CLOAKED, ctypes.byref(cloaked), 4
            )
            visible = bool(user32.IsWindowVisible(hwnd))
            if buf.value or visible:
                print(
                    f"pid={pid.value} title={buf.value!r} visible={visible} "
                    f"iconic={bool(user32.IsIconic(hwnd))} cloaked={cloaked.value}"
                )
        return True

    user32.EnumWindows(ENUM_PROC(visit), 0)


if __name__ == "__main__":
    main()
