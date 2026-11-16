from friday.listening_indicator import ListeningIndicator
from friday.ui_events import State, StateChanged, UiEventBus


def make(busy=False):
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    state = {"busy": busy}
    indicator = ListeningIndicator(bus, lambda: state["busy"])
    return indicator, got, state


def test_press_shows_listening_when_free():
    indicator, got, _ = make()
    indicator.on_press()
    assert got == [StateChanged(State.LISTENING)]


def test_press_while_busy_shows_nothing():
    indicator, got, _ = make(busy=True)
    indicator.on_press()
    indicator.on_release()
    assert got == []


def test_short_press_returns_to_idle_on_release():
    indicator, got, _ = make()
    indicator.on_press()
    indicator.on_release()
    assert got == [StateChanged(State.LISTENING), StateChanged(State.IDLE)]


def test_accepted_audio_leaves_state_to_the_assistant():
    indicator, got, _ = make()
    indicator.on_press()
    indicator.on_audio_submitted(True)
    indicator.on_release()
    assert got == [StateChanged(State.LISTENING)]


def test_dropped_audio_returns_to_idle():
    indicator, got, _ = make()
    indicator.on_press()
    indicator.on_audio_submitted(False)
    indicator.on_release()
    assert got == [StateChanged(State.LISTENING), StateChanged(State.IDLE)]
