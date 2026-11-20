import time

import numpy as np
import pytest

from friday.level_meter import LevelMeter
from friday.level_publisher import QUEUE_SIZE, LevelPublisher
from friday.ui_events import LevelChanged, State, StateChanged, UiEventBus


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class FakeRecorder:
    def __init__(self) -> None:
        self.listeners = []

    def add_listener(self, listener) -> None:
        self.listeners.append(listener)

    def remove_listener(self, listener) -> None:
        self.listeners.remove(listener)


def frame(amplitude: float, size: int = 480) -> np.ndarray:
    return np.full(size, amplitude, dtype=np.float32)


def levels(got):
    return [e for e in got if isinstance(e, LevelChanged)]


def make():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    clock = FakeClock()
    publisher = LevelPublisher(bus, FakeRecorder(), meter=LevelMeter(clock=clock))
    return bus, got, clock, publisher


def test_nothing_is_published_when_not_listening():
    bus, got, clock, publisher = make()
    clock.now = 0.06
    publisher.handle_frame(frame(0.05))
    assert levels(got) == []


def test_level_is_published_while_listening():
    bus, got, clock, publisher = make()
    bus.publish(StateChanged(State.LISTENING))
    clock.now = 0.06
    publisher.handle_frame(frame(0.05))
    assert len(levels(got)) == 1
    assert levels(got)[0].level == pytest.approx(0.7, abs=0.01)


def test_zero_is_sent_once_when_listening_ends():
    bus, got, clock, publisher = make()
    bus.publish(StateChanged(State.LISTENING))
    clock.now = 0.06
    publisher.handle_frame(frame(0.05))
    bus.publish(StateChanged(State.IDLE))
    clock.now = 0.12
    publisher.handle_frame(frame(0.05))
    assert levels(got)[-1] == LevelChanged(0.0)
    assert len(levels(got)) == 2
    clock.now = 0.18
    publisher.handle_frame(frame(0.05))
    assert len(levels(got)) == 2


def test_state_published_before_the_publisher_is_known():
    bus = UiEventBus()
    bus.publish(StateChanged(State.LISTENING))
    got = []
    bus.subscribe(got.append)
    clock = FakeClock()
    publisher = LevelPublisher(bus, FakeRecorder(), meter=LevelMeter(clock=clock))
    clock.now = 0.06
    publisher.handle_frame(frame(0.05))
    assert len(levels(got)) == 1


def test_full_queue_drops_frames_without_blocking():
    bus, got, clock, publisher = make()
    for _ in range(QUEUE_SIZE + 50):
        publisher.on_frame(frame(0.05))


def test_started_publisher_works_in_its_own_thread():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    bus.publish(StateChanged(State.LISTENING))
    recorder = FakeRecorder()
    publisher = LevelPublisher(bus, recorder, meter=LevelMeter(interval=0.01))
    publisher.start()
    try:
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not levels(got):
            recorder.listeners[0](frame(0.05))
            time.sleep(0.01)
    finally:
        publisher.close()
    assert levels(got)
    assert recorder.listeners == []
