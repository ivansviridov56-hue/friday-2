"""Global mouse side-button trigger (Windows), built on pynput.

The hook thread only decodes the event and queues the callback. A worker thread
runs the callbacks, because opening the microphone inside a Windows low-level
hook is slow, and a slow hook gets skipped by the system.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Callable

log = logging.getLogger(__name__)

WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP = 0x020C
WM_XBUTTONDBLCLK = 0x020D
XBUTTON1 = 1  # "back"
XBUTTON2 = 2  # "forward"

_ACTIONS = {WM_XBUTTONDOWN: "down", WM_XBUTTONUP: "up", WM_XBUTTONDBLCLK: "dblclk"}

ListenerFactory = Callable[[Callable[[int, int], bool]], Any]


def decode_xbutton(msg: int, mouse_data: int) -> tuple[int, str] | None:
    """Return (button number, action) for side-button messages, else None."""
    action = _ACTIONS.get(msg)
    if action is None:
        return None
    return (mouse_data >> 16) & 0xFFFF, action


def _default_listener_factory(on_event: Callable[[int, int], bool]) -> Any:
    from pynput import mouse

    def event_filter(msg: int, data: Any) -> bool:
        if on_event(msg, data.mouseData):
            listener.suppress_event()  # type: ignore[attr-defined]  # raises: the event never reaches other apps
        return True

    listener = mouse.Listener(win32_event_filter=event_filter)
    return listener


class SideButtonTrigger:
    def __init__(
        self,
        button: int,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        suppress: bool = True,
        listener_factory: ListenerFactory | None = None,
    ) -> None:
        if button not in (XBUTTON1, XBUTTON2):
            raise ValueError("button must be XBUTTON1 or XBUTTON2")
        self._button = button
        self._on_press = on_press
        self._on_release = on_release
        self._suppress = suppress
        self._listener_factory = listener_factory or _default_listener_factory
        self._queue: queue.SimpleQueue[Callable[[], None] | None] = queue.SimpleQueue()
        self._listener: Any = None
        self._worker: threading.Thread | None = None

    def handle(self, msg: int, mouse_data: int) -> bool:
        """Process one raw mouse event. Return True if it must be swallowed."""
        decoded = decode_xbutton(msg, mouse_data)
        if decoded is None:
            return False
        button, action = decoded
        log.debug("side button event: X%d %s", button, action)
        if button != self._button:
            return False
        if action == "down":
            self._queue.put(self._on_press)
        elif action == "up":
            self._queue.put(self._on_release)
        return self._suppress

    def _work(self) -> None:
        while True:
            callback = self._queue.get()
            if callback is None:
                return
            try:
                callback()
            except Exception:
                log.exception("trigger callback failed")

    def start(self) -> None:
        if self._worker is not None:
            return
        self._worker = threading.Thread(
            target=self._work, name="mouse-trigger", daemon=True
        )
        self._worker.start()
        self._listener = self._listener_factory(self.handle)
        self._listener.start()

    def stop(self) -> None:
        if self._worker is None:
            return
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._queue.put(None)
        self._worker.join(timeout=5)
        self._worker = None
