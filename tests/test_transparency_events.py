from friday.ui_bridge import UiBridge
from friday.ui_events import ThemeChanged, TransparencyChanged, UiEventBus


def test_late_subscriber_gets_theme_then_transparency():
    bus = UiEventBus()
    bus.publish(TransparencyChanged(30))
    bus.publish(ThemeChanged("black"))
    got = []
    bus.subscribe(got.append)
    assert got == [ThemeChanged("black"), TransparencyChanged(30)]


def test_bus_remembers_only_the_last_transparency():
    bus = UiEventBus()
    bus.publish(TransparencyChanged(10))
    bus.publish(TransparencyChanged(55))
    got = []
    bus.subscribe(got.append)
    assert got == [TransparencyChanged(55)]


def test_bridge_calls_set_transparency():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(TransparencyChanged(42))
    assert scripts == ["window.fridayUi.setTransparency(42)"]
