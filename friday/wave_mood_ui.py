"""UI Automation side of starting My Wave with a mood.

Implements the WaveMoodUi protocol from wave_mood.py on top of the Yandex Music
window. Names and behaviour were checked live with ym_mood_press_probe: the
settings button exists only while no mood is selected (and may have size 0x0),
mood buttons toggle (get_toggle_state 1 = selected), a plate "Сбросить <Mood> и
включить Мою волну" shows the current mood and resets it. Everything is pressed
with invoke() only: no mouse movement.

pywinauto and the Win32 helpers are imported lazily, so this module can be
imported (and tested with fakes) without them.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from friday.wave_mood import WaveMoodLauncher, mood_from_name

logger = logging.getLogger(__name__)

WAVE_LINK = "yandexmusic://radio/user/onyourwave"

OPEN_NAME = "настроить мою волну"
CLOSE_NAME = "закрыть меню настроек"
RESET_PREFIX = "сбросить "
RESET_SUFFIX = " и включить мою волну"


def clean(text: str | None) -> str:
    """Button name for comparison: no non-breaking spaces, trimmed, lower case."""
    return (text or "").replace("\xa0", " ").strip().lower()


def mood_from_reset_name(name: str | None) -> str | None:
    """Mood key from a plate name like 'Сбросить Весёлое и включить Мою волну'."""
    text = clean(name)
    if not (text.startswith(RESET_PREFIX) and text.endswith(RESET_SUFFIX)):
        return None
    middle = text[len(RESET_PREFIX) : len(text) - len(RESET_SUFFIX)]
    return mood_from_name(middle) if middle else None


class UiaWaveMoodUi:
    def __init__(
        self,
        window,
        *,
        settle: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._window = window
        self._settle = settle
        self._sleep = sleep

    def _buttons(self, visible_only: bool = True) -> list[tuple[str, Any]]:
        found: list[tuple[str, Any]] = []
        for button in self._window.descendants(control_type="Button"):
            try:
                info = button.element_info
                if visible_only:
                    rect = info.rectangle
                    if rect.width() <= 0 or rect.height() <= 0:
                        continue
                found.append((clean(info.name), button))
            except Exception:
                continue
        return found

    def _visible_named(self, name: str) -> list:
        return [b for n, b in self._buttons() if n == name]

    def _mood_buttons(self, mood: str) -> list:
        return [b for n, b in self._buttons() if mood_from_name(n) == mood]

    def current_mood(self) -> str | None:
        for name, _button in self._buttons():
            mood = mood_from_reset_name(name)
            if mood is not None:
                return mood
        return None

    def reset_mood(self) -> None:
        for name, button in self._buttons():
            if mood_from_reset_name(name) is not None:
                button.invoke()
                return
        raise RuntimeError("no reset button")

    def panel_open(self) -> bool:
        return bool(self._visible_named(CLOSE_NAME))

    def open_panel(self) -> bool:
        if self.panel_open():
            return True
        candidates = [b for n, b in self._buttons(visible_only=False) if n == OPEN_NAME]
        if not candidates:
            logger.info("settings button not found")
            return False
        for button in candidates:
            try:
                button.invoke()
            except Exception as error:
                logger.debug("open invoke failed: %s", type(error).__name__)
                continue
            self._sleep(self._settle)
            if self.panel_open():
                return True
        return False

    def press_mood(self, mood: str) -> None:
        targets = self._mood_buttons(mood)
        if len(targets) != 1:
            raise RuntimeError(f"expected one mood button, found {len(targets)}")
        if self._is_selected(targets[0]):
            return  # pressing a selected mood would unselect it
        targets[0].invoke()

    def mood_selected(self, mood: str) -> bool:
        targets = self._mood_buttons(mood)
        return len(targets) == 1 and self._is_selected(targets[0])

    def close_panel(self) -> None:
        targets = self._visible_named(CLOSE_NAME)
        if targets:
            targets[0].invoke()

    @staticmethod
    def _is_selected(button) -> bool:
        try:
            return button.get_toggle_state() == 1
        except Exception:
            return False


def find_ui() -> UiaWaveMoodUi | None:
    from friday.ym_ui import _find_window

    window = _find_window()
    return UiaWaveMoodUi(window) if window is not None else None


def build_launcher() -> WaveMoodLauncher:
    """Live-checked only (needs the Yandex Music window)."""
    from friday.playback_check import make_is_any_playing
    from friday.smtc import list_sessions
    from friday.wave_ui import _WindowRestorer
    from friday.ym_ui import _pids, open_link

    restorer = _WindowRestorer()
    return WaveMoodLauncher(
        find_ui,
        make_is_any_playing(list_sessions),
        prepare=restorer.prepare,
        after_start=restorer.minimize_back,
        is_running=lambda: bool(_pids()),
        open_wave=lambda: open_link(WAVE_LINK),
    )
