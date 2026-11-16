import pytest

from friday.mouse_trigger import (
    WM_XBUTTONDBLCLK,
    WM_XBUTTONDOWN,
    WM_XBUTTONUP,
    XBUTTON1,
    XBUTTON2,
    SideButtonTrigger,
    decode_xbutton,
)


def raw(button: int) -> int:
    """mouseData of a side-button message: the button number is in the high word."""
    return button << 16


class FakeListener:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def make_trigger(on_press=None, on_release=None, suppress=True, button=XBUTTON2):
    calls: list[str] = []
    listener = FakeListener()
    captured: dict = {}

    def factory(on_event):
        captured["on_event"] = on_event
        return listener

    trigger = SideButtonTrigger(
        button,
        on_press or (lambda: calls.append("press")),
        on_release or (lambda: calls.append("release")),
        suppress=suppress,
        listener_factory=factory,
    )
    trigger.start()
    return trigger, captured["on_event"], calls, listener


def test_decode_down_and_up() -> None:
    assert decode_xbutton(WM_XBUTTONDOWN, raw(2)) == (2, "down")
    assert decode_xbutton(WM_XBUTTONUP, raw(1)) == (1, "up")


def test_decode_ignores_low_word() -> None:
    assert decode_xbutton(WM_XBUTTONDOWN, raw(2) | 0x1234) == (2, "down")


def test_decode_ignores_other_messages() -> None:
    assert decode_xbutton(0x0201, 0) is None  # left button down


def test_dispatches_press_and_release_in_order() -> None:
    trigger, on_event, calls, _ = make_trigger()
    on_event(WM_XBUTTONDOWN, raw(XBUTTON2))
    on_event(WM_XBUTTONUP, raw(XBUTTON2))
    trigger.stop()
    assert calls == ["press", "release"]


def test_other_side_button_is_ignored_and_not_swallowed() -> None:
    trigger, on_event, calls, _ = make_trigger()
    assert on_event(WM_XBUTTONDOWN, raw(XBUTTON1)) is False
    assert on_event(WM_XBUTTONUP, raw(XBUTTON1)) is False
    trigger.stop()
    assert calls == []


def test_selected_button_is_swallowed() -> None:
    trigger, on_event, _, _ = make_trigger()
    assert on_event(WM_XBUTTONDOWN, raw(XBUTTON2)) is True
    assert on_event(WM_XBUTTONUP, raw(XBUTTON2)) is True
    trigger.stop()


def test_double_click_message_is_swallowed_without_dispatch() -> None:
    trigger, on_event, calls, _ = make_trigger()
    assert on_event(WM_XBUTTONDBLCLK, raw(XBUTTON2)) is True
    trigger.stop()
    assert calls == []


def test_suppress_false_dispatches_but_does_not_swallow() -> None:
    trigger, on_event, calls, _ = make_trigger(suppress=False)
    assert on_event(WM_XBUTTONDOWN, raw(XBUTTON2)) is False
    trigger.stop()
    assert calls == ["press"]


def test_start_and_stop_control_listener() -> None:
    trigger, _, _, listener = make_trigger()
    assert listener.started and not listener.stopped
    trigger.stop()
    assert listener.stopped


def test_callback_error_does_not_stop_worker() -> None:
    def bad() -> None:
        raise RuntimeError("boom")

    trigger, on_event, calls, _ = make_trigger(on_press=bad)
    on_event(WM_XBUTTONDOWN, raw(XBUTTON2))
    on_event(WM_XBUTTONUP, raw(XBUTTON2))
    trigger.stop()
    assert calls == ["release"]


def test_stop_without_start_is_safe() -> None:
    trigger = SideButtonTrigger(
        XBUTTON2, lambda: None, lambda: None, listener_factory=lambda f: FakeListener()
    )
    trigger.stop()


def test_invalid_button_is_rejected() -> None:
    with pytest.raises(ValueError):
        SideButtonTrigger(5, lambda: None, lambda: None)
