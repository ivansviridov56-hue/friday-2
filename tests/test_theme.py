import pytest

from friday.theme import DEFAULT_THEME, THEMES, parse_theme
from friday.ui_bridge import UiBridge
from friday.ui_events import (
    CirclesStyleChanged,
    State,
    StateChanged,
    ThemeChanged,
    UiEventBus,
)


@pytest.mark.parametrize("name", THEMES)
def test_known_themes_are_kept(name):
    assert parse_theme(name) == name


@pytest.mark.parametrize("value", [None, "", "   ", "pink"])
def test_missing_or_unknown_gives_default(value):
    assert parse_theme(value) == DEFAULT_THEME


def test_case_and_spaces_are_ignored():
    assert parse_theme("  Windows ") == "windows"


def test_default_is_a_known_theme():
    assert DEFAULT_THEME in THEMES


def test_bridge_sends_theme_to_page():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(ThemeChanged("black"))
    assert scripts == ['window.fridayUi.setTheme("black")']


def test_theme_before_page_is_loaded_is_queued():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.on_event(ThemeChanged("windows"))
    assert scripts == []
    bridge.mark_ready()
    assert scripts == ['window.fridayUi.setTheme("windows")']


def test_late_subscriber_gets_the_theme():
    bus = UiEventBus()
    bus.publish(ThemeChanged("black"))
    got = []
    bus.subscribe(got.append)
    assert got == [ThemeChanged("black")]


def test_late_subscriber_gets_only_the_latest_theme():
    bus = UiEventBus()
    bus.publish(ThemeChanged("black"))
    bus.publish(ThemeChanged("windows"))
    got = []
    bus.subscribe(got.append)
    assert got == [ThemeChanged("windows")]


def test_late_subscriber_gets_theme_state_and_style_in_order():
    bus = UiEventBus()
    bus.publish(CirclesStyleChanged("dots"))
    bus.publish(StateChanged(State.IDLE))
    bus.publish(ThemeChanged("black"))
    got = []
    bus.subscribe(got.append)
    assert got == [
        ThemeChanged("black"),
        StateChanged(State.IDLE),
        CirclesStyleChanged("dots"),
    ]
