import json

from friday.ui_bridge import UiBridge
from friday.ui_events import MessageAdded, State, StateChanged


def state_js(name):
    return f"window.fridayUi.setState({json.dumps(name)})"


def message_js(role, text):
    return f"window.fridayUi.addMessage({json.dumps(role)}, {json.dumps(text)})"


def test_events_before_ready_are_queued_then_flushed_in_order():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.on_event(StateChanged(State.THINKING))
    bridge.on_event(MessageAdded("user", "привет"))
    assert scripts == []
    bridge.mark_ready()
    assert scripts == [state_js("thinking"), message_js("user", "привет")]


def test_events_after_ready_run_immediately():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(StateChanged(State.SPEAKING))
    assert scripts == [state_js("speaking")]


def test_text_with_quotes_and_newlines_stays_one_safe_literal():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    text = 'Он сказал "привет"\nи ушёл</script>'
    bridge.on_event(MessageAdded("assistant", text))
    assert scripts == [message_js("assistant", text)]
    assert "\n" not in scripts[0]


def test_failing_window_does_not_raise():
    def broken(_script):
        raise RuntimeError("window closed")

    bridge = UiBridge(broken)
    bridge.mark_ready()
    bridge.on_event(StateChanged(State.IDLE))
