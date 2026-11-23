from friday.ui_bridge import UiBridge
from friday.ui_events import UiEventBus, WallpaperChanging


def test_bridge_turns_the_event_into_a_call():
    calls = []
    bridge = UiBridge(calls.append)
    bridge.mark_ready()
    bridge.on_event(WallpaperChanging())
    assert calls == ["window.fridayUi.wallpaperChanging()"]


def test_event_before_the_page_is_ready_is_dropped():
    calls = []
    bridge = UiBridge(calls.append)
    bridge.on_event(WallpaperChanging())
    bridge.mark_ready()
    assert calls == []


def test_bus_does_not_replay_it_to_a_late_subscriber():
    bus = UiEventBus()
    bus.publish(WallpaperChanging())
    got = []
    bus.subscribe(got.append)
    assert got == []
