"""Windows calls for the blurred window background. Live-checked, no unit tests."""

from __future__ import annotations

import ctypes
import logging
import sys
import threading

from friday.backdrop_logic import enable_backdrop, make_tint

log = logging.getLogger(__name__)

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
CORNER_ROUND = 2
WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_ACRYLIC = 4
ACCENT_FLAGS = 2


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class _CompositionData(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


class _Margins(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int) for n in ("left", "right", "top", "bottom")]


def _paint_form_black(window: object) -> None:
    """Glass shows through pure black painted by the form, so make the form black."""
    try:
        from System import Action  # type: ignore[import-not-found]
        from System.Drawing import Color  # type: ignore[import-not-found]

        form = window.native  # type: ignore[attr-defined]

        def paint() -> None:
            form.BackColor = Color.Black

        form.Invoke(Action(paint))
    except Exception:
        log.exception("could not set the form colour")


def _apply_once(title: str, extend: bool) -> bool:
    """One application of the blur. `extend` says whether the glass covers the whole window."""
    user32 = ctypes.windll.user32
    dwm = ctypes.windll.dwmapi
    user32.FindWindowW.restype = ctypes.c_void_p
    user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    user32.SetWindowCompositionAttribute.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    dwm.DwmSetWindowAttribute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_uint,
    ]
    dwm.DwmExtendFrameIntoClientArea.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    hwnd = user32.FindWindowW(None, title)
    if not hwnd:
        log.error("window handle not found")
        return False

    for attr, value in (
        (DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
        (DWMWA_WINDOW_CORNER_PREFERENCE, CORNER_ROUND),
    ):
        number = ctypes.c_int(value)
        dwm.DwmSetWindowAttribute(
            hwnd, attr, ctypes.byref(number), ctypes.sizeof(number)
        )

    side = -1 if extend else 0
    dwm.DwmExtendFrameIntoClientArea(
        hwnd, ctypes.byref(_Margins(side, side, side, side))
    )

    policy = _AccentPolicy(ACCENT_ENABLE_ACRYLIC, ACCENT_FLAGS, make_tint(), 0)
    data = _CompositionData(
        WCA_ACCENT_POLICY,
        ctypes.cast(ctypes.byref(policy), ctypes.c_void_p),
        ctypes.sizeof(policy),
    )
    return bool(user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data)))


def start_backdrop(window: object, title: str) -> None:
    """Turn the blur on in a background thread (the steps include a short pause)."""

    def apply(extend: bool) -> bool:
        ok = _apply_once(title, extend)
        _paint_form_black(window)
        return ok

    def work() -> None:
        try:
            enabled = enable_backdrop(apply, sys.getwindowsversion().build)
        except Exception:
            log.exception("backdrop failed")
            return
        log.info("backdrop: %s", "on" if enabled else "off (plain window)")

    threading.Thread(target=work, daemon=True, name="backdrop").start()
