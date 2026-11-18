"""UI Automation side of starting My Wave in the Yandex Music window.

Live-checked, no unit tests. The player block is found by structure, never by
name: a visible group whose direct children hold exactly two sliders and at
least three buttons; the target is the middle one of the last three buttons, pressed only if it is named "Воспроизведение".
If there is not exactly one such group, nothing is returned and nothing is
pressed.
"""

from __future__ import annotations

import logging

from friday.playback_check import make_is_any_playing
from friday.smtc import list_sessions
from friday.wave_launcher import WaveLauncher
from friday.ym_ui import _descendants, _find_window

logger = logging.getLogger(__name__)


class UiaWavePlayer:
    def __init__(self, button) -> None:
        self._button = button

    def press_play(self) -> None:
        # invoke() only: no mouse movement, no real click as a fallback.
        self._button.invoke()


def _transport_buttons(group) -> list | None:
    try:
        if group.rectangle().width() <= 0:
            return None
        kids = group.children()
        sliders = [k for k in kids if k.element_info.control_type == "Slider"]
        buttons = [k for k in kids if k.element_info.control_type == "Button"]
    except Exception:
        return None
    if len(sliders) == 2 and len(buttons) >= 3:
        return buttons
    return None


_PLAY_NAME = "Воспроизведение"


def _middle_button(buttons: list):
    """The middle of the last three buttons, or None if it is not a Play button.

    Structure finds the group; the name is only a safety check before pressing,
    so a similar-looking group (the bottom bar: queue / sound settings / mute)
    is never pressed.
    """
    middle = buttons[-3:][1]
    try:
        name = middle.element_info.name
    except Exception:
        return None
    return middle if name == _PLAY_NAME else None


def find_player() -> UiaWavePlayer | None:
    window = _find_window()
    if window is None:
        return None
    found = [
        button
        for button in (
            _middle_button(buttons)
            for buttons in map(_transport_buttons, _descendants(window, "Group"))
            if buttons is not None
        )
        if button is not None
    ]
    if len(found) != 1:
        logger.info("expected one wave player, found %d", len(found))
        return None
    return UiaWavePlayer(found[0])


def build_launcher() -> WaveLauncher:
    return WaveLauncher(find_player, make_is_any_playing(list_sessions))
