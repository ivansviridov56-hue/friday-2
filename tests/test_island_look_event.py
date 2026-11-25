from friday.ui_events import IslandLookChanged, ThemeChanged, UiEventBus


def collect(bus):
    got = []
    bus.subscribe(got.append)
    return got


def test_a_listener_gets_a_published_look():
    bus = UiEventBus()
    got = collect(bus)
    bus.publish(IslandLookChanged("eyes"))
    assert got == [IslandLookChanged("eyes")]


def test_a_late_listener_gets_the_last_look():
    bus = UiEventBus()
    bus.publish(IslandLookChanged("eyes"))
    bus.publish(IslandLookChanged("equalizer"))
    assert collect(bus) == [IslandLookChanged("equalizer")]


def test_without_a_look_nothing_extra_is_replayed():
    bus = UiEventBus()
    bus.publish(ThemeChanged("black"))
    assert collect(bus) == [ThemeChanged("black")]
