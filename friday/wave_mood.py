"""Start My Wave with a chosen mood (calm, cheerful, ...) and confirm it.

Pure logic: everything that touches the Yandex Music window is injected, so it
is covered by tests. The UI side (finding buttons by name) comes in a later step.
Chain: other mood selected -> reset it; open the settings panel; press the mood;
check the button state and that something plays; close the panel.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Callable, Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

MOOD_NAMES = {
    "active": "Бодрое",
    "fun": "Весёлое",
    "calm": "Спокойное",
    "sad": "Грустное",
}


def _norm(text: str) -> str:
    return (text or "").replace("\xa0", " ").strip().lower().replace("ё", "е")


_BY_NAME = {_norm(name): mood for mood, name in MOOD_NAMES.items()}


def mood_from_name(name: str) -> str | None:
    """Mood key for a button / plate name like 'Весёлое', or None."""
    return _BY_NAME.get(_norm(name))


class MoodStatus(Enum):
    STARTED = "started"
    ALREADY_SET = "already_set"
    NO_WINDOW = "no_window"
    NO_PANEL = "no_panel"
    NOT_CONFIRMED = "not_confirmed"
    ERROR = "error"


class WaveMoodUi(Protocol):
    def current_mood(self) -> str | None: ...
    def reset_mood(self) -> None: ...
    def open_panel(self) -> bool: ...
    def panel_open(self) -> bool: ...
    def press_mood(self, mood: str) -> None: ...
    def mood_selected(self, mood: str) -> bool: ...
    def close_panel(self) -> None: ...


class WaveMoodLauncher:
    def __init__(
        self,
        find_ui: Callable[[], WaveMoodUi | None],
        is_playing: Callable[[], bool],
        *,
        prepare: Callable[[], None] | None = None,
        after_start: Callable[[], None] | None = None,
        is_running: Callable[[], bool] | None = None,
        open_wave: Callable[[], None] | None = None,
        cold_start_timeout: float = 20.0,
        window_timeout: float = 5.0,
        panel_timeout: float = 5.0,
        confirm_timeout: float = 5.0,
        poll_interval: float = 0.3,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._find_ui = find_ui
        self._is_playing = is_playing
        self._prepare = prepare
        self._after_start = after_start
        self._is_running = is_running
        self._open_wave = open_wave
        self._cold_start_timeout = cold_start_timeout
        self._window_timeout = window_timeout
        self._panel_timeout = panel_timeout
        self._confirm_timeout = confirm_timeout
        self._interval = poll_interval
        self._sleep = sleep
        self._monotonic = monotonic

    def launch(self, mood: str) -> MoodStatus:
        if mood not in MOOD_NAMES:
            logger.warning("unknown mood requested")
            return MoodStatus.ERROR
        self._safe(self._prepare)
        try:
            return self._run(mood)
        except Exception as error:
            logger.warning("mood launch failed: %s", type(error).__name__)
            return MoodStatus.ERROR
        finally:
            self._safe(self._after_start)

    def _run(self, mood: str) -> MoodStatus:
        timeout = self._window_timeout
        if self._start_app_if_closed():
            timeout = self._cold_start_timeout
        ui = self._poll(self._safe_find, timeout, lambda v: v is not None)
        if ui is None:
            logger.info("Yandex Music window not found")
            return MoodStatus.NO_WINDOW
        current = ui.current_mood()
        if current == mood and self._safe_playing():
            return MoodStatus.ALREADY_SET
        if current is not None:
            ui.reset_mood()
            if not self._poll(
                lambda: ui.current_mood() is None, self._confirm_timeout, bool
            ):
                logger.info("reset did not clear the mood")
                return MoodStatus.NOT_CONFIRMED
        if not self._poll(ui.open_panel, self._panel_timeout, bool):
            return MoodStatus.NO_PANEL
        if not self._poll(ui.panel_open, self._panel_timeout, bool):
            return MoodStatus.NO_PANEL
        ui.press_mood(mood)
        selected = self._poll(
            lambda: ui.mood_selected(mood), self._confirm_timeout, bool
        )
        playing = selected and self._poll(
            self._safe_playing, self._confirm_timeout, bool
        )
        try:
            ui.close_panel()
        except Exception as error:
            logger.debug("closing the panel failed: %s", type(error).__name__)
        return MoodStatus.STARTED if playing else MoodStatus.NOT_CONFIRMED

    def _start_app_if_closed(self) -> bool:
        if self._is_running is None or self._open_wave is None:
            return False
        try:
            if self._is_running():
                return False
            self._open_wave()
        except Exception as error:
            logger.warning("cold start failed: %s", type(error).__name__)
            return False
        logger.info("Yandex Music is closed: opened the wave link")
        return True

    def _safe(self, func: Callable[[], None] | None) -> None:
        if func is None:
            return
        try:
            func()
        except Exception as error:
            logger.debug("step failed: %s", type(error).__name__)

    def _safe_find(self) -> WaveMoodUi | None:
        try:
            return self._find_ui()
        except Exception as error:
            logger.debug("window lookup failed: %s", type(error).__name__)
            return None

    def _safe_playing(self) -> bool:
        try:
            return bool(self._is_playing())
        except Exception as error:
            logger.debug("playback check failed: %s", type(error).__name__)
            return False

    def _poll(self, check: Callable[[], T], timeout: float, ok: Callable[[T], bool]):
        deadline = self._monotonic() + timeout
        while True:
            value = check()
            if ok(value):
                return value
            if self._monotonic() >= deadline:
                return None
            self._sleep(self._interval)
