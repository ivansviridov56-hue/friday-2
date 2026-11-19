import logging
import threading

import numpy as np
import pytest

from friday.speech_segmenter import SAMPLE_RATE
from friday.wake_listener import WakeListener

FRAME = np.zeros(480, dtype=np.float32)


def phrase(seconds: float = 1.0) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds), dtype=np.float32)


class FakeSegmenter:
    """Returns the phrases queued in `emit` on the next feed()."""

    def __init__(self) -> None:
        self.emit: list[np.ndarray] = []
        self.in_speech = False
        self.feeds = 0
        self.resets = 0

    def feed(self, samples: np.ndarray) -> list[np.ndarray]:
        self.feeds += 1
        out, self.emit = self.emit, []
        return out

    def reset(self) -> None:
        self.resets += 1


class FakeStt:
    def __init__(self, *texts: str | Exception) -> None:
        self.texts = list(texts)
        self.calls = 0

    def transcribe(self, audio: np.ndarray) -> str:
        self.calls += 1
        item = self.texts.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeMic:
    def __init__(self) -> None:
        self.listeners: list = []

    def add_listener(self, listener) -> None:
        self.listeners.append(listener)

    def remove_listener(self, listener) -> None:
        self.listeners.remove(listener)


class Rig:
    def __init__(self, *texts: str | Exception, **kwargs) -> None:
        self.t = [100.0]
        self.busy = [False]
        self.segmenter = FakeSegmenter()
        self.stt = FakeStt(*texts)
        self.sent: list[str] = []
        self.events: list[str] = []
        self.accept = True
        self.mic = FakeMic()

        def submit(text: str) -> bool:
            self.sent.append(text)
            return self.accept

        self.listener = WakeListener(
            self.mic,
            self.stt,
            submit,
            lambda: self.busy[0],
            segmenter=self.segmenter,
            on_event=self.events.append,
            clock=lambda: self.t[0],
            **kwargs,
        )

    def hear(self, seconds: float = 1.0) -> None:
        """One frame arrives and the segmenter hands over a finished phrase."""
        self.segmenter.emit = [phrase(seconds)]
        self.listener.process(FRAME)


def test_name_with_a_command_sends_the_command_without_the_name() -> None:
    rig = Rig("Пятница, что на экране?")
    rig.hear()
    assert rig.sent == ["что на экране?"]
    assert rig.events == ["command"]


def test_phrase_without_the_name_is_ignored() -> None:
    rig = Rig("Включи свет", "В пятницу поедем на дачу", "Включи музыку, Пятница")
    for _ in range(3):
        rig.hear()
    assert rig.sent == [] and rig.events == []
    assert rig.stt.calls == 3


def test_name_alone_waits_for_the_next_phrase() -> None:
    rig = Rig("Пятница.", "Что на экране?")
    rig.hear()
    assert rig.sent == [] and rig.events == ["wake"]
    rig.t[0] += 3
    rig.hear()
    assert rig.sent == ["Что на экране?"]
    assert rig.events == ["wake", "command"]


def test_next_phrase_after_the_wait_is_just_conversation() -> None:
    rig = Rig("Пятница", "Что на экране?")
    rig.hear()
    rig.t[0] += 10
    rig.hear()
    assert rig.sent == []


def test_a_long_command_that_started_in_time_is_accepted() -> None:
    rig = Rig("Пятница", "Включи песню номер один")
    rig.hear()
    rig.segmenter.in_speech = True  # the user is speaking the command
    rig.t[0] += 8  # the phrase ended late, but it began 5 s into the wait
    rig.hear(seconds=3.5)
    assert rig.sent == ["Включи песню номер один"]


def test_wait_times_out_and_says_so() -> None:
    rig = Rig("Пятница")
    rig.hear()
    rig.t[0] += 7
    rig.listener.process(FRAME)
    assert rig.events == ["wake", "timeout"]


def test_wait_does_not_expire_while_the_user_is_speaking() -> None:
    rig = Rig("Пятница")
    rig.hear()
    rig.t[0] += 7
    rig.segmenter.in_speech = True
    rig.listener.process(FRAME)
    assert rig.events == ["wake"]


def test_noise_while_waiting_keeps_waiting() -> None:
    rig = Rig("Пятница", "", "Пауза")
    rig.hear()
    rig.hear()
    assert rig.sent == []
    rig.hear()
    assert rig.sent == ["Пауза"]


def test_name_again_while_waiting_restarts_the_wait() -> None:
    rig = Rig("Пятница", "Пятница!")
    rig.hear()
    rig.t[0] += 5
    rig.hear()
    rig.t[0] += 5  # 10 s after the first name, 5 s after the second
    rig.listener.process(FRAME)
    assert rig.events == ["wake", "wake"]


def test_command_with_the_name_while_waiting_loses_the_name() -> None:
    rig = Rig("Пятница", "Пятница, пауза")
    rig.hear()
    rig.hear()
    assert rig.sent == ["пауза"]


def test_deaf_while_the_assistant_is_busy() -> None:
    rig = Rig("Пятница, пауза")
    rig.busy[0] = True
    rig.hear()
    assert rig.segmenter.feeds == 0 and rig.stt.calls == 0
    assert rig.segmenter.resets == 1


def test_still_deaf_for_a_moment_after_the_assistant_finished() -> None:
    rig = Rig("Пятница, пауза")
    rig.busy[0] = True
    rig.listener.process(FRAME)
    rig.busy[0] = False
    rig.t[0] += 0.5
    rig.hear()
    assert rig.sent == []  # the tail of her own voice
    rig.t[0] += 1.0
    rig.hear()
    assert rig.sent == ["пауза"]


def test_busy_cancels_the_wait() -> None:
    rig = Rig("Пятница")
    rig.hear()
    rig.busy[0] = True
    rig.listener.process(FRAME)
    assert rig.events == ["wake", "cancel"]


def test_recognition_error_does_not_stop_the_listener() -> None:
    rig = Rig(RuntimeError("boom"), "Пятница, пауза")
    rig.hear()
    rig.hear()
    assert rig.sent == ["пауза"]


def test_command_dropped_by_the_assistant_is_not_reported_as_sent() -> None:
    rig = Rig("Пятница, пауза")
    rig.accept = False
    rig.hear()
    assert rig.sent == ["пауза"]
    assert rig.events == []


def test_broken_submit_and_broken_event_handler_are_survived() -> None:
    rig = Rig("Пятница, пауза", "Пятница, дальше")

    def bad_submit(text: str) -> bool:
        raise RuntimeError("boom")

    def bad_event(name: str) -> None:
        raise RuntimeError("boom")

    rig.listener._submit = bad_submit
    rig.hear()
    rig.listener._on_event = bad_event
    rig.listener._submit = lambda text: True
    rig.hear()


def test_texts_are_not_logged_by_default(caplog: pytest.LogCaptureFixture) -> None:
    rig = Rig("Пятница, секретная фраза")
    with caplog.at_level(logging.INFO):
        rig.hear()
    assert "секретная" not in caplog.text
    assert "phrase 1.0 s" in caplog.text


def test_texts_are_logged_when_asked(caplog: pytest.LogCaptureFixture) -> None:
    rig = Rig("Пятница, пауза", log_text=True)
    with caplog.at_level(logging.INFO):
        rig.hear()
    assert "пауза" in caplog.text


def test_start_subscribes_and_stop_unsubscribes() -> None:
    rig = Rig()
    rig.listener.start()
    rig.listener.start()
    assert len(rig.mic.listeners) == 1
    rig.listener.stop()
    assert rig.mic.listeners == []
    rig.listener.stop()


def test_frames_from_the_microphone_reach_the_logic_in_a_worker_thread() -> None:
    rig = Rig("Пятница, пауза")
    done = threading.Event()
    rig.segmenter.emit = [phrase()]

    def submit(text: str) -> bool:
        rig.sent.append(text)
        done.set()
        return True

    rig.listener._submit = submit
    rig.listener.start()
    try:
        rig.mic.listeners[0](FRAME)  # what the audio thread does
        assert done.wait(2.0)
    finally:
        rig.listener.stop()
    assert rig.sent == ["пауза"]


def test_a_full_queue_drops_frames_instead_of_blocking() -> None:
    rig = Rig(queue_frames=2)
    for _ in range(5):
        rig.listener._enqueue(FRAME)  # no worker running: must not block or raise
    assert rig.listener._queue.qsize() == 2
