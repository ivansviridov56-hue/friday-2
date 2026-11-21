"""Watches the Yandex Music session and sends the current cover to the window."""

from __future__ import annotations

import logging
import threading
from typing import Protocol

from friday.cover_data import to_data_url
from friday.ui_events import CoverChanged, UiEventBus

log = logging.getLogger(__name__)

POLL_SECONDS = 2.0


class CoverSource(Protocol):
    def key(self) -> tuple[str, str] | None:
        """(title, artist) of the current track, None if Music is closed or idle."""

    def cover(self) -> bytes | None:
        """Raw image bytes of the current cover, None if there is none."""


class CoverPublisher:
    """Publishes CoverChanged when the track changes or Music goes away."""

    def __init__(
        self, bus: UiEventBus, source: CoverSource, interval: float = POLL_SECONDS
    ) -> None:
        self._bus = bus
        self._source = source
        self._interval = interval
        self._last_key: tuple[str, str] | None = None
        self._last_url: str | None = None
        self._failing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def poll_once(self) -> None:
        try:
            self._poll()
            self._failing = False
        except Exception:
            if not self._failing:
                log.exception("cover polling failed")
            self._failing = True

    def _poll(self) -> None:
        key = self._source.key()
        if key == self._last_key and (key is None or self._last_url is not None):
            return
        url = to_data_url(self._source.cover()) if key is not None else None
        if key == self._last_key and url == self._last_url:
            return
        self._last_key, self._last_url = key, url
        self._bus.publish(CoverChanged(url))

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name="cover-publisher", daemon=True
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
