import json

from friday.ui_bridge import UiBridge
from friday.ui_events import AccentChanged, UiEventBus


def test_bus_replays_only_the_last_accent_to_a_late_subscriber():
    bus = UiEventBus()
    bus.publish(AccentChanged("#111111", "#222222"))
    bus.publish(AccentChanged("#333333", "#444444"))
    got = []
    bus.subscribe(got.append)
    assert got == [AccentChanged("#333333", "#444444")]


def test_bridge_sends_the_accent_variables():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(AccentChanged("#4cc2ff", "#99ebff"))
    prefix = "window.fridayUi.setAccent("
    assert len(scripts) == 1 and scripts[0].startswith(prefix)
    payload = json.loads(scripts[0][len(prefix) : -1])
    assert payload["--accent"] == "#4cc2ff"
    assert payload["--accent-rgb"] == "76, 194, 255"
