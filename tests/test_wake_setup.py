import threading
import time

import numpy as np
import pytest

from friday.ui_events import State, StateChanged, UiEventBus
from friday.wake_setup import SerializedTranscriber, WakeIndicator, env_flag


@pytest.mark.parametrize("value", ["1", "true", "TRUE", " yes ", "On", "on"])
def test_env_flag_true_values(value: str) -> None:
    assert env_flag(value) is True


@pytest.mark.parametrize("value", [None, "", "0", "false", "no", "off", "2", "maybe"])
def test_env_flag_everything_else_is_off(value) -> None:
    assert env_flag(value) is False


def make_indicator():
    bus = UiEventBus()
    got: list = []
    bus.subscribe(got.append)
    return WakeIndicator(bus), got


def test_wake_shows_listening() -> None:
    indicator, got = make_indicator()
    indicator.on_event("wake")
    assert got == [StateChanged(State.LISTENING)]


def test_timeout_returns_to_idle() -> None:
    indicator, got = make_indicator()
    indicator.on_event("wake")
    indicator.on_event("timeout")
    assert got == [StateChanged(State.LISTENING), StateChanged(State.IDLE)]


@pytest.mark.parametrize("name", ["command", "cancel", "something-else"])
def test_other_events_leave_the_window_alone(name: str) -> None:
    indicator, got = make_indicator()
    indicator.on_event(name)
    assert got == []


class SlowStt:
    def __init__(self) -> None:
        self.running = 0
        self.max_running = 0
        self._guard = threading.Lock()

    def transcribe(self, audio: np.ndarray) -> str:
        with self._guard:
            self.running += 1
            self.max_running = max(self.max_running, self.running)
        time.sleep(0.03)
        with self._guard:
            self.running -= 1
        return "текст"


def test_serialized_transcriber_runs_one_recognition_at_a_time() -> None:
    inner = SlowStt()
    shared = SerializedTranscriber(inner)
    results: list[str] = []
    threads = [
        threading.Thread(
            target=lambda: results.append(
                shared.transcribe(np.zeros(5, dtype=np.float32))
            )
        )
        for _ in range(6)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert results == ["текст"] * 6
    assert inner.max_running == 1


def test_unserialized_stt_would_overlap() -> None:
    """Sanity check of the test itself: without the wrapper the calls do overlap."""
    inner = SlowStt()
    threads = [
        threading.Thread(target=lambda: inner.transcribe(np.zeros(5, dtype=np.float32)))
        for _ in range(6)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert inner.max_running > 1
