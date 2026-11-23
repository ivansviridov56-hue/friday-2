"""Watches the Windows accent colour and sends it to the window."""

from __future__ import annotations

import logging
import threading
from typing import Protocol

from friday.accent_logic import parse_palette, pick_accent
from friday.ui_events import AccentChanged, UiEventBus

log = logging.getLogger(__name__)

POLL_SECONDS = 0.5


class AccentSource(Protocol):
    def palette(self) -> bytes | None:
        """Raw AccentPalette bytes, None if there are none."""


class AccentPublisher:
    """Publishes AccentChanged when the accent changes (the wallpaper slideshow changes it)."""

    def __init__(
        self, bus: UiEventBus, source: AccentSource, interval: float = POLL_SECONDS
    ) -> None:
        self._bus = bus
        self._source = source
        self._interval = interval
        self._last: tuple[str, str] | None = None
        self._failing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def poll_once(self) -> None:
        try:
            self._poll()
            self._failing = False
        except Exception:
            if not self._failing:
                log.exception("accent polling failed")
            self._failing = True

    def _poll(self) -> None:
        data = self._source.palette()
        if data is None:
            return
        colors = pick_accent(parse_palette(data))
        if colors == self._last:
            return
        self._last = colors
        self._bus.publish(AccentChanged(*colors))

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name="accent-publisher", daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        self.poll_once()
        while not self._stop.wait(self._interval):
            self.poll_once()
