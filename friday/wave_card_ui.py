"""UI Automation side of starting a My Wave card.

Implements the WaveCardUi protocol from wave_card_launcher.py on top of the
Yandex Music window. Checked live with the card probes: cards are Group or
Button controls anywhere in the window, a card can have several copies, and only
the copy with a non-zero size is in view. Invoking a hidden copy just scrolls
the carousel. Everything is pressed with invoke() only: no mouse movement.

pywinauto and the Win32 helpers are imported lazily, so this module can be
imported (and tested with fakes) without them.
"""

from __future__ import annotations

import logging
from typing import Any, Iterator

from friday.wave_card_launcher import WaveCardLauncher
from friday.wave_cards import parse_card

logger = logging.getLogger(__name__)

CARD_TYPES = ("Group", "Button")


class UiaWaveCardUi:
    def __init__(self, window) -> None:
        self._window = window

    def _cards(self) -> Iterator[tuple[str, str, Any]]:
        """(raw name, normalized name, control) for every wave card copy."""
        for control_type in CARD_TYPES:
            for control in self._window.descendants(control_type=control_type):
                try:
                    raw = control.element_info.name or ""
                except Exception:  # a control can vanish while walking
                    continue
                card = parse_card(raw)
                if card is not None:
                    yield raw, card.name, control

    def _copies(self, name: str) -> list:
        return [control for _, found, control in self._cards() if found == name]

    def card_names(self) -> list[str]:
        return [raw for raw, _, _ in self._cards()]

    def card_visible(self, name: str) -> bool:
        return any(self._has_size(control) for control in self._copies(name))

    def press_card(self, name: str) -> bool:
        copies = self._copies(name)
        visible = [control for control in copies if self._has_size(control)]
        # Never fall back from a visible copy to a hidden one: that would only
        # scroll, while the launcher would believe the card was really pressed.
        for control in visible or copies:
            try:
                control.invoke()
                return True
            except Exception as error:
                logger.debug("card invoke failed: %s", type(error).__name__)
        return False

    @staticmethod
    def _has_size(control) -> bool:
        try:
            rect = control.element_info.rectangle
            return rect.width() > 0 and rect.height() > 0
        except Exception:
            return False


def find_ui() -> UiaWaveCardUi | None:
    from friday.ym_ui import _find_window

    window = _find_window()
    return UiaWaveCardUi(window) if window is not None else None


def build_launcher() -> WaveCardLauncher:
    """Live-checked only (needs the Yandex Music window)."""
    from friday.playback_check import make_is_any_playing
    from friday.smtc import list_sessions
    from friday.wave_ui import _WindowRestorer

    restorer = _WindowRestorer()
    return WaveCardLauncher(
        find_ui,
        make_is_any_playing(list_sessions),
        prepare=restorer.prepare,
        after_start=restorer.minimize_back,
    )
