"""Windows calls for the blurred window background. Live-checked, no unit tests."""

from __future__ import annotations

import ctypes
import logging
import sys
import threading

from collections.abc import Callable

from friday.backdrop_logic import (
    CHANGE_STEPS,
    DEFAULT_OPACITY,
    DEFAULT_TINT,
    enable_backdrop,
    make_tint,
    run_steps,
)

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


def _apply_once(title: str, extend: bool, color: str, opacity: float) -> bool:
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

    policy = _AccentPolicy(
        ACCENT_ENABLE_ACRYLIC, ACCENT_FLAGS, make_tint(color, opacity)
    )
    data = _CompositionData(
        WCA_ACCENT_POLICY,
        ctypes.cast(ctypes.byref(policy), ctypes.c_void_p),
        ctypes.sizeof(policy),
    )
    return bool(user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data)))


class Backdrop:
    """The blurred window background; its tint can change while the window runs."""

    def __init__(
        self,
        window: object,
        title: str,
        on_ready: Callable[[], object] | None = None,
    ) -> None:
        self._on_ready = on_ready
        self._window = window
        self._title = title
        self._lock = threading.Lock()
        self._wanted: tuple[str, float] = (DEFAULT_TINT, DEFAULT_OPACITY)
        self._applied: tuple[str, float] | None = None
        self._enabled = False
        self._worker: threading.Thread | None = None

    def start(self) -> None:
        """Turn the blur on in a background thread (the steps include a short pause)."""
        with self._lock:
            if self._worker is None and not self._enabled:
                self._launch(self._first_run)

    def set_tint(self, color: str, opacity: float) -> None:
        """Ask for a new tint (colour '#rrggbb', opacity 0..1). Any thread, also before start()."""
        with self._lock:
            self._wanted = (color, opacity)
            if self._enabled and self._worker is None and self._wanted != self._applied:
                self._launch(self._change_loop)

    def _launch(self, target) -> None:  # the caller holds the lock
        thread = threading.Thread(target=target, daemon=True, name="backdrop")
        self._worker = thread
        thread.start()

    def _apply_step(self, extend: bool) -> bool:
        with self._lock:
            color, opacity = self._wanted
        ok = _apply_once(self._title, extend, color, opacity)
        _paint_form_black(self._window)
        if ok:
            with self._lock:
                self._applied = (color, opacity)
        return ok

    def _first_run(self) -> None:
        try:
            enabled = enable_backdrop(self._apply_step, sys.getwindowsversion().build)
        except Exception:
            log.exception("backdrop failed")
            enabled = False
        log.info("backdrop: %s", "on" if enabled else "off (plain window)")
        with self._lock:
            self._enabled = enabled
        if self._on_ready is not None:
            self._on_ready()  # also when the blur is off: the window must appear
        self._change_loop()

    def _change_loop(self) -> None:
        while True:
            with self._lock:
                if not self._enabled or self._wanted == self._applied:
                    self._worker = None
                    return
            if not run_steps(self._apply_step, CHANGE_STEPS):
                log.warning("could not change the tint")
                with self._lock:
                    self._worker = None
                return
