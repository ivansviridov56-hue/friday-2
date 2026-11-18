"""UI Automation side of starting an artist in the Yandex Music window.

Live-checked, no unit tests. The artist page has a yellow play button
("Воспроизведение") whose nearest container holds an "Исполнитель" mark and
exactly ONE play button outside nested lists. The page title and the big heading
are not reliable in the UI tree, so the artist is identified by the "Артист <name>"
links of the popular tracks: the most frequent name wins, a tie means "unknown".
Nothing is clicked unless the expected artist is the one on the page.
"""

from __future__ import annotations

from collections import Counter

from friday.artist_playback import make_is_artist_playing
from friday.smtc import list_sessions
from friday.track_launcher import LaunchResult, TrackLauncher, normalize
from friday.ym_ui import (
    MAX_LEVELS,
    PLAY_NAME,
    UiaTrackPanel,
    _descendants,
    _find_window,
    _key,
    _label,
    _own_plays,
    open_link,
)

ARTIST_MARK = "исполнитель"
LINK_PREFIX = "артист "


def _has_mark(container) -> bool:
    return any(
        _label(t).lower() == ARTIST_MARK for t in _descendants(container, "Text")
    )


def _top_artist(container) -> str | None:
    names: Counter[str] = Counter()
    for link in _descendants(container, "Hyperlink"):
        label = _label(link)
        if label.lower().startswith(LINK_PREFIX):
            name = normalize(label[len(LINK_PREFIX) :])
            if name:
                names[name] += 1
    ranked = names.most_common(2)
    if not ranked:
        return None
    if len(ranked) == 2 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def _artist_panel_around(button) -> UiaTrackPanel | None:
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
        if _has_mark(node):
            # The yellow "Слушать" button is the first own play button in tree
            # order; the release cover button comes after it.
            if not own or _key(own[0]) != me:
                return None
            top = own[0].rectangle().top
            if any(b.rectangle().top < top for b in own[1:]):
                return None  # order and position disagree: do not guess
            name = _top_artist(node)
            return UiaTrackPanel(button, name) if name else None
        if len(own) > 1:
            return None  # too high and no artist mark: not the artist panel
    return None


def find_artist_panel() -> UiaTrackPanel | None:
    window = _find_window()
    if window is None:
        return None
    plays = [
        b for b in _descendants(window, "Button") if _label(b).lower() == PLAY_NAME
    ]
    panels = [p for p in map(_artist_panel_around, plays) if p is not None]
    return panels[0] if len(panels) == 1 else None


class ArtistLauncher:
    """Same launch(link, name) contract as TrackLauncher, for artist pages."""

    def launch(self, link: str, title: str) -> LaunchResult:
        wanted = normalize(title)

        def find() -> UiaTrackPanel | None:
            panel = find_artist_panel()
            # A stale page of another artist counts as "not found yet": keep polling.
            if panel is None or normalize(panel.title) != wanted:
                return None
            return panel

        launcher = TrackLauncher(
            open_link,
            find,
            make_is_artist_playing(list_sessions),
            panel_timeout=15.0,
        )
        return launcher.launch(link, title)


def build_artist_launcher() -> ArtistLauncher:
    return ArtistLauncher()
