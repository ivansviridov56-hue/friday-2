from friday.ui_events import MessageAdded, State, StateChanged, UiEventBus


def test_listener_receives_events_in_order():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    bus.publish(StateChanged(State.LISTENING))
    bus.publish(MessageAdded("user", "привет"))
    assert got == [StateChanged(State.LISTENING), MessageAdded("user", "привет")]


def test_publish_without_listeners_is_ok():
    UiEventBus().publish(StateChanged(State.IDLE))


def test_broken_listener_does_not_block_others():
    bus = UiEventBus()
    got = []

    def broken(_event):
        raise RuntimeError("boom")

    bus.subscribe(broken)
    bus.subscribe(got.append)
    bus.publish(StateChanged(State.THINKING))
    assert got == [StateChanged(State.THINKING)]


def test_unsubscribe_stops_delivery():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    bus.unsubscribe(got.append)
    bus.publish(StateChanged(State.SPEAKING))
    assert got == []


def test_late_subscriber_gets_the_last_state():
    bus = UiEventBus()
    bus.publish(StateChanged(State.LOADING))
    bus.publish(StateChanged(State.IDLE))
    got = []
    bus.subscribe(got.append)
    assert got == [StateChanged(State.IDLE)]


def test_late_subscriber_does_not_get_old_messages():
    bus = UiEventBus()
    bus.publish(MessageAdded("user", "привет"))
    got = []
    bus.subscribe(got.append)
    assert got == []


def test_loading_state_value_for_the_page():
    assert State.LOADING.value == "loading"
