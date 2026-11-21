import pytest

from friday.circles_style import CIRCLE_STYLES, DEFAULT_STYLE, parse_circles_style
from friday.ui_bridge import UiBridge
from friday.ui_events import CirclesStyleChanged, StateChanged, State, UiEventBus


@pytest.mark.parametrize("name", CIRCLE_STYLES)
def test_known_styles_are_kept(name):
    assert parse_circles_style(name) == name


@pytest.mark.parametrize("value", [None, "", "   ", "sparkles"])
def test_missing_or_unknown_gives_default(value):
    assert parse_circles_style(value) == DEFAULT_STYLE


def test_case_and_spaces_are_ignored():
    assert parse_circles_style("  Equalizer ") == "equalizer"


def test_default_is_a_known_style():
    assert DEFAULT_STYLE in CIRCLE_STYLES


def test_bridge_sends_style_to_page():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(CirclesStyleChanged("blobs"))
    assert scripts == ['window.fridayUi.setCirclesStyle("blobs")']


def test_style_before_page_is_loaded_is_queued():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.on_event(CirclesStyleChanged("dots"))
    assert scripts == []
    bridge.mark_ready()
    assert scripts == ['window.fridayUi.setCirclesStyle("dots")']


def test_late_subscriber_gets_the_style():
    bus = UiEventBus()
    bus.publish(CirclesStyleChanged("equalizer"))
    got = []
    bus.subscribe(got.append)
    assert got == [CirclesStyleChanged("equalizer")]


def test_late_subscriber_gets_only_the_latest_style_and_the_state():
    bus = UiEventBus()
    bus.publish(CirclesStyleChanged("blobs"))
    bus.publish(StateChanged(State.IDLE))
    bus.publish(CirclesStyleChanged("dots"))
    got = []
    bus.subscribe(got.append)
    assert got == [StateChanged(State.IDLE), CirclesStyleChanged("dots")]
