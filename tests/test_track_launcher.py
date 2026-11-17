from typing import Callable

import pytest

from friday.track_launcher import LaunchStatus, TrackLauncher, normalize


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class FakePanel:
    def __init__(
        self,
        title: str = "Song",
        on_press: Callable[[], None] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.title = title
        self.presses = 0
        self._on_press = on_press
        self._error = error

    def press_play(self) -> None:
        self.presses += 1
        if self._error:
            raise self._error
        if self._on_press:
            self._on_press()


def sequence(*values):
    """Return values one by one, then repeat the last; an Exception is raised."""
    items = list(values)

    def call(*_args):
        value = items.pop(0) if len(items) > 1 else items[0]
        if isinstance(value, Exception):
            raise value
        return value

    return call


def make(find_panel, is_playing, open_link=None):
    clock = Clock()
    opened: list[str] = []
    launcher = TrackLauncher(
        open_link or opened.append,
        find_panel,
        is_playing,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    return launcher, opened, clock


def playing_after_press():
    state = {"playing": False}
    panel = FakePanel(on_press=lambda: state.update(playing=True))
    return panel, (lambda title: state["playing"])


def test_starts_and_confirms():
    panel, is_playing = playing_after_press()
    launcher, opened, _ = make(lambda: panel, is_playing)
    result = launcher.launch("yandexmusic://album/1/track/2", "Song")
    assert result.status is LaunchStatus.STARTED
    assert result.found_title == "Song"
    assert opened == ["yandexmusic://album/1/track/2"]
    assert panel.presses == 1


def test_already_playing_is_not_clicked():
    panel = FakePanel()
    launcher, _, _ = make(lambda: panel, lambda title: True)
    assert launcher.launch("link", "Song").status is LaunchStatus.ALREADY_PLAYING
    assert panel.presses == 0


def test_no_panel():
    launcher, _, clock = make(lambda: None, lambda title: False)
    assert launcher.launch("link", "Song").status is LaunchStatus.NO_PANEL
    assert clock.now >= 6.0


def test_panel_appearing_late():
    panel, is_playing = playing_after_press()
    launcher, _, _ = make(sequence(None, None, panel), is_playing)
    assert launcher.launch("link", "Song").status is LaunchStatus.STARTED


def test_wrong_track_is_not_clicked():
    panel = FakePanel(title="Another song")
    launcher, _, _ = make(lambda: panel, lambda title: False)
    result = launcher.launch("link", "Song")
    assert result.status is LaunchStatus.WRONG_TRACK
    assert result.found_title == "Another song"
    assert panel.presses == 0


def test_title_match_ignores_case_yo_and_spaces():
    panel = FakePanel(title="  ЁЛКА   Ту ")
    launcher, _, _ = make(lambda: panel, lambda title: True)
    assert launcher.launch("link", "елка ту").status is LaunchStatus.ALREADY_PLAYING


def test_press_not_confirmed():
    panel = FakePanel()
    launcher, _, _ = make(lambda: panel, lambda title: False)
    assert launcher.launch("link", "Song").status is LaunchStatus.NOT_CONFIRMED
    assert panel.presses == 1


def test_open_error():
    calls = []

    def find_panel():
        calls.append(1)
        return FakePanel()

    def broken_open(link):
        raise OSError("no handler")

    launcher, _, _ = make(find_panel, lambda title: False, open_link=broken_open)
    assert launcher.launch("link", "Song").status is LaunchStatus.ERROR
    assert calls == []


def test_press_error():
    panel = FakePanel(error=RuntimeError("ui"))
    launcher, _, _ = make(lambda: panel, lambda title: False)
    assert launcher.launch("link", "Song").status is LaunchStatus.ERROR


def test_find_panel_error_is_retried():
    panel, is_playing = playing_after_press()
    launcher, _, _ = make(sequence(RuntimeError("ui"), panel), is_playing)
    assert launcher.launch("link", "Song").status is LaunchStatus.STARTED


def test_playing_check_error_counts_as_not_playing():
    panel = FakePanel()
    launcher, _, _ = make(lambda: panel, sequence(RuntimeError("smtc"), False, True))
    assert launcher.launch("link", "Song").status is LaunchStatus.STARTED
    assert panel.presses == 1


def test_link_is_opened_before_panel_search():
    events: list[str] = []
    panel = FakePanel()
    answers = iter([False, False, True])

    def find_panel():
        events.append("find")
        return panel

    launcher, _, _ = make(
        find_panel,
        lambda title: next(answers, True),
        open_link=lambda link: events.append("open"),
    )
    launcher.launch("link", "Song")
    assert events[0] == "open"
    assert "find" in events


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Hello  World", "hello world"), ("Ёлка", "елка"), ("  x ", "x"), (None, "")],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_already_playing_skips_link_and_panel():
    events = []
    launcher = TrackLauncher(
        lambda link: events.append("open"),
        lambda: events.append("find"),
        lambda title: True,
    )
    result = launcher.launch("link", "Song")
    assert result.status is LaunchStatus.ALREADY_PLAYING
    assert events == []
