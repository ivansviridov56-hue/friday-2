"""Start a found Yandex Music track and confirm that it really plays.

Pure logic: opening the link, finding the track panel and asking "is it playing"
are injected, so everything here is covered by tests. The UI side lives elsewhere.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LaunchStatus(Enum):
    STARTED = "started"
    ALREADY_PLAYING = "already_playing"
    NO_PANEL = "no_panel"
    WRONG_TRACK = "wrong_track"
    NOT_CONFIRMED = "not_confirmed"
    ERROR = "error"


@dataclass(frozen=True)
class LaunchResult:
    status: LaunchStatus
    found_title: str | None = None


class TrackPanel(Protocol):
    @property
    def title(self) -> str: ...

    def press_play(self) -> None: ...


def normalize(text: str | None) -> str:
    """Lower-case, fold "ё" to "е" and collapse whitespace."""
    return " ".join((text or "").lower().replace("ё", "е").split())


class TrackLauncher:
    def __init__(
        self,
        open_link: Callable[[str], None],
        find_panel: Callable[[], TrackPanel | None],
        is_playing: Callable[[str], bool],
        *,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        panel_timeout: float = 6.0,
        confirm_timeout: float = 5.0,
        poll_interval: float = 0.3,
    ) -> None:
        self._open_link = open_link
        self._find_panel = find_panel
        self._is_playing = is_playing
        self._sleep = sleep
        self._monotonic = monotonic
        self._panel_timeout = panel_timeout
        self._confirm_timeout = confirm_timeout
        self._interval = poll_interval

    def launch(self, link: str, title: str) -> LaunchResult:
        try:
            self._open_link(link)
        except Exception as error:
            logger.warning("opening the track link failed: %s", type(error).__name__)
            return LaunchResult(LaunchStatus.ERROR)

        panel = self._poll(
            self._safe_panel, self._panel_timeout, lambda v: v is not None
        )
        if panel is None:
            logger.info("track panel not found")
            return LaunchResult(LaunchStatus.NO_PANEL)

        try:
            found = panel.title
        except Exception as error:
            logger.warning("reading the panel title failed: %s", type(error).__name__)
            return LaunchResult(LaunchStatus.ERROR)

        if normalize(found) != normalize(title):
            logger.info("panel shows %r, expected %r", found, title)
            return LaunchResult(LaunchStatus.WRONG_TRACK, found)

        if self._safe_playing(title):
            return LaunchResult(LaunchStatus.ALREADY_PLAYING, found)

        try:
            panel.press_play()
        except Exception as error:
            logger.warning("pressing play failed: %s", type(error).__name__)
            return LaunchResult(LaunchStatus.ERROR, found)

        confirmed = self._poll(
            lambda: self._safe_playing(title), self._confirm_timeout, bool
        )
        if confirmed:
            return LaunchResult(LaunchStatus.STARTED, found)
        logger.info("play was pressed but the session does not report playback")
        return LaunchResult(LaunchStatus.NOT_CONFIRMED, found)

    def _safe_panel(self) -> TrackPanel | None:
        try:
            return self._find_panel()
        except Exception as error:
            logger.debug("panel lookup failed: %s", type(error).__name__)
            return None

    def _safe_playing(self, title: str) -> bool:
        try:
            return bool(self._is_playing(title))
        except Exception as error:
            logger.debug("playback check failed: %s", type(error).__name__)
            return False

    def _poll(
        self, check: Callable[[], T], timeout: float, ok: Callable[[T], bool]
    ) -> T | None:
        deadline = self._monotonic() + timeout
        while True:
            value = check()
            if ok(value):
                return value
            if self._monotonic() >= deadline:
                return None
            self._sleep(self._interval)
