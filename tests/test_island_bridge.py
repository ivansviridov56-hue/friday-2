from friday.island_bridge import IslandBridge
from friday.ui_events import (
    LevelChanged,
    MessageAdded,
    State,
    StateChanged,
    UiEventBus,
    ThemeChanged,
)


class FakeIsland:
    def __init__(self) -> None:
        self.states: list[str] = []
        self.themes: list[str] = []
        self.calls: list[str] = []
        self.texts: list[str] = []
        self.clears = 0
        self.reveals: list[str] = []
        self.chunks: list[tuple[int, int, float]] = []
        self.finishes = 0

    def set_state(self, state: str) -> None:
        self.states.append(state)
        self.calls.append(f"state:{state}")

    def set_theme(self, theme: str) -> None:
        self.themes.append(theme)
        self.calls.append(f"theme:{theme}")

    def show_text(self, text: str) -> None:
        self.texts.append(text)

    def clear_text(self) -> None:
        self.clears += 1

    def start_reveal(self, text: str) -> None:
        self.reveals.append(text)

    def reveal_chunk(self, start: int, end: int, seconds: float) -> None:
        self.chunks.append((start, end, seconds))

    def finish_reveal(self) -> None:
        self.finishes += 1


class FakeTimer:
    def __init__(self, delay, callback) -> None:
        self.delay = delay
        self.callback = callback
        self.daemon = False
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if not self.cancelled:
            self.callback()


def make_with_timers():
    bus = UiEventBus()
    island = FakeIsland()
    timers: list[FakeTimer] = []

    def factory(delay, callback):
        timers.append(FakeTimer(delay, callback))
        return timers[-1]

    bridge = IslandBridge(bus, island, timer_factory=factory)
    bridge.start()
    return bus, island, bridge, timers


def test_assistant_message_shows_text():
    bus, island, _, _ = make_with_timers()
    bus.publish(MessageAdded("assistant", "Hi,   how are you?", spoken=False))
    assert island.texts == ["Hi, how are you?"]


def test_user_message_is_not_shown():
    bus, island, _, _ = make_with_timers()
    bus.publish(MessageAdded("user", "привет"))
    assert island.texts == []


def test_blank_message_is_not_shown():
    bus, island, _, _ = make_with_timers()
    bus.publish(MessageAdded("assistant", "   "))
    assert island.texts == []


def test_text_is_hidden_1_5_seconds_after_speech_ends():
    bus, island, _, timers = make_with_timers()
    bus.publish(MessageAdded("assistant", "Ответ"))
    bus.publish(StateChanged(State.SPEAKING))
    assert timers == []
    bus.publish(StateChanged(State.IDLE))
    assert len(timers) == 1 and timers[0].delay == 1.5 and timers[0].started
    timers[0].fire()
    assert island.clears == 1


def test_speaking_cancels_a_pending_hide():
    bus, island, _, timers = make_with_timers()
    bus.publish(MessageAdded("assistant", "Ответ"))
    bus.publish(StateChanged(State.IDLE))
    bus.publish(StateChanged(State.SPEAKING))
    assert timers[0].cancelled
    timers[0].fire()
    assert island.clears == 0


def test_new_message_cancels_a_pending_hide():
    bus, island, _, timers = make_with_timers()
    bus.publish(MessageAdded("assistant", "One", spoken=False))
    bus.publish(StateChanged(State.IDLE))
    bus.publish(MessageAdded("assistant", "Two", spoken=False))
    assert timers[0].cancelled
    assert island.texts == ["One", "Two"]


def test_idle_without_text_schedules_nothing():
    bus, _, _, timers = make_with_timers()
    bus.publish(StateChanged(State.IDLE))
    assert timers == []


def test_unspoken_reply_is_hidden_too():
    bus, island, _, timers = make_with_timers()
    bus.publish(StateChanged(State.THINKING))
    bus.publish(MessageAdded("assistant", "Next one.", spoken=False))
    bus.publish(StateChanged(State.IDLE))
    timers[-1].fire()
    assert island.clears == 1


def test_close_cancels_a_pending_hide():
    bus, island, bridge, timers = make_with_timers()
    bus.publish(MessageAdded("assistant", "Ответ"))
    bus.publish(StateChanged(State.IDLE))
    bridge.close()
    assert timers[0].cancelled


def make() -> tuple[UiEventBus, FakeIsland, IslandBridge]:
    bus = UiEventBus()
    island = FakeIsland()
    return bus, island, IslandBridge(bus, island)


def test_state_is_forwarded_as_text():
    bus, island, bridge = make()
    bridge.start()
    bus.publish(StateChanged(State.LISTENING))
    assert island.states == ["listening"]


def test_other_events_are_ignored():
    bus, island, bridge = make()
    bridge.start()
    bus.publish(MessageAdded("user", "привет"))
    bus.publish(LevelChanged(0.5))
    assert island.states == []


def test_late_start_gets_the_last_state():
    bus, island, bridge = make()
    bus.publish(StateChanged(State.THINKING))
    bridge.start()
    assert island.states == ["thinking"]


def test_close_stops_forwarding():
    bus, island, bridge = make()
    bridge.start()
    bridge.close()
    bus.publish(StateChanged(State.SPEAKING))
    assert island.states == []


def test_start_twice_subscribes_once():
    bus, island, bridge = make()
    bridge.start()
    bridge.start()
    bus.publish(StateChanged(State.IDLE))
    assert island.states == ["idle"]


def test_close_without_start_is_safe():
    _, _, bridge = make()
    bridge.close()


def test_theme_is_forwarded():
    bus, island, bridge = make()
    bridge.start()
    bus.publish(ThemeChanged("windows"))
    assert island.themes == ["windows"]


def test_late_start_gets_the_theme_before_the_state():
    bus, island, bridge = make()
    bus.publish(StateChanged(State.IDLE))
    bus.publish(ThemeChanged("black"))
    bridge.start()
    assert island.calls == ["theme:black", "state:idle"]
