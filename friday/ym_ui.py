"""UI Automation side of starting a track in the Yandex Music window.

Live-checked, no unit tests. The panel is found by structure, never by name or
size alone: the nearest container that holds a "Закрыть" button, a "Трек" mark
and a title, and exactly ONE "Воспроизведение" button. If the situation is
ambiguous, nothing is returned and nothing is clicked.
"""

from __future__ import annotations

import logging
import os
import subprocess

from pywinauto import Application

from friday.playback_check import make_is_playing
from friday.smtc import list_sessions
from friday.track_launcher import TrackLauncher

logger = logging.getLogger(__name__)

EXE_NAMES = ("Яндекс Музыка.exe", "YandexMusic.exe")
PLAY_NAME = "воспроизведение"
CLOSE_NAME = "закрыть"
TRACK_MARK = "трек"
MAX_LEVELS = 5


def _label(element) -> str:
    try:
        return (element.window_text() or "").strip()
    except Exception:
        return ""


def _descendants(container, control_type: str) -> list:
    try:
        return container.descendants(control_type=control_type)
    except Exception:
        return []


def _pids() -> list[int]:
    pids: list[int] = []
    for exe in EXE_NAMES:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
            ).decode("cp866", errors="ignore")
        except Exception:
            continue
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.strip().split(",")]
            if len(parts) > 1 and parts[1].isdigit():
                pids.append(int(parts[1]))
    return pids


def _find_window():
    for pid in _pids():
        try:
            windows = (
                Application(backend="uia")
                .connect(process=pid)
                .windows(visible_only=True)
            )
        except Exception:
            continue
        if windows:
            titled = [w for w in windows if _label(w)]
            return (titled or windows)[0]
    return None


def _title_after_mark(container) -> str | None:
    texts = [_label(t) for t in _descendants(container, "Text")]
    lowered = [t.lower() for t in texts]
    if TRACK_MARK not in lowered:
        return None
    for text in texts[lowered.index(TRACK_MARK) + 1 :]:
        if text:
            return text
    return None


class UiaTrackPanel:
    def __init__(self, button, title: str) -> None:
        self._button = button
        self.title = title

    def press_play(self) -> None:
        # invoke() only: no mouse movement, and no real click as a fallback,
        # because a click by coordinates could land on the wrong control.
        self._button.invoke()


def _key(element):
    try:
        return tuple(element.element_info.runtime_id)
    except Exception:
        return id(element)  # unknown identity: nothing matches, so we fail safe


def _own_plays(container) -> list:
    """Play buttons of a container, not counting rows of nested lists."""
    plays = [
        b for b in _descendants(container, "Button") if _label(b).lower() == PLAY_NAME
    ]
    in_lists = {
        _key(b)
        for lst in _descendants(container, "List")
        for b in _descendants(lst, "Button")
        if _label(b).lower() == PLAY_NAME
    }
    return [b for b in plays if _key(b) not in in_lists]


def _panel_around(button) -> UiaTrackPanel | None:
    me = _key(button)
    node = button
    for _ in range(MAX_LEVELS):
        try:
            node = node.parent()
        except Exception:
            return None
        if node is None:
            return None
        own = _own_plays(node)
        if len(own) > 1:
            return None  # too high: the album button is inside as well
        buttons = _descendants(node, "Button")
        has_close = any(_label(b).lower() == CLOSE_NAME for b in buttons)
        title = _title_after_mark(node)
        if has_close and title:
            if len(own) == 1 and _key(own[0]) == me:
                return UiaTrackPanel(button, title)
            return None  # this is a panel, but the button is not its own
    return None


def find_panel() -> UiaTrackPanel | None:
    window = _find_window()
    if window is None:
        return None
    plays = [
        b for b in _descendants(window, "Button") if _label(b).lower() == PLAY_NAME
    ]
    panels = [p for p in map(_panel_around, plays) if p is not None]
    return panels[0] if len(panels) == 1 else None


def open_link(uri: str) -> None:
    os.startfile(uri)  # type: ignore[attr-defined]  # Windows only


def build_launcher() -> TrackLauncher:
    return TrackLauncher(
        open_link,
        find_panel,
        make_is_playing(list_sessions),
        panel_timeout=15.0,
    )
