from friday.ui_bridge import UiBridge
from friday.ui_events import LevelChanged, MessageAdded, UiEventBus


def make():
    calls = []
    return UiBridge(calls.append), calls


def test_level_becomes_a_js_call():
    bridge, calls = make()
    bridge.mark_ready()
    bridge.on_event(LevelChanged(0.5))
    assert calls == ["window.fridayUi.setLevel(0.500)"]


def test_level_is_clamped_to_zero_one():
    bridge, calls = make()
    bridge.mark_ready()
    bridge.on_event(LevelChanged(1.7))
    bridge.on_event(LevelChanged(-0.2))
    assert calls == [
        "window.fridayUi.setLevel(1.000)",
        "window.fridayUi.setLevel(0.000)",
    ]


def test_level_before_the_page_is_ready_is_dropped():
    bridge, calls = make()
    bridge.on_event(LevelChanged(0.5))
    bridge.on_event(MessageAdded("user", "hi"))
    bridge.mark_ready()
    assert len(calls) == 1
    assert "addMessage" in calls[0]


def test_bus_does_not_replay_a_level_to_a_late_subscriber():
    bus = UiEventBus()
    bus.publish(LevelChanged(0.5))
    got = []
    bus.subscribe(got.append)
    assert got == []
