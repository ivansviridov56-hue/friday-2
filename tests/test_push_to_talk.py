import numpy as np

from friday.push_to_talk import PushToTalk


class FakeRecorder:
    def __init__(self, audio: np.ndarray) -> None:
        self.audio = audio
        self.starts = 0
        self.stops = 0

    def start(self) -> None:
        self.starts += 1

    def stop(self) -> np.ndarray:
        self.stops += 1
        return self.audio


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def make_ptt(min_duration: float = 0.3):
    recorder = FakeRecorder(np.ones(16000, dtype=np.float32))
    clock = FakeClock()
    delivered: list[np.ndarray] = []
    ptt = PushToTalk(recorder, delivered.append, min_duration=min_duration, clock=clock)
    return ptt, recorder, clock, delivered


def test_press_starts_recording() -> None:
    ptt, recorder, _, _ = make_ptt()
    ptt.press()
    assert recorder.starts == 1


def test_release_delivers_audio() -> None:
    ptt, _, clock, delivered = make_ptt()
    ptt.press()
    clock.now = 1.0
    ptt.release()
    assert len(delivered) == 1 and delivered[0].size == 16000


def test_short_press_is_discarded() -> None:
    ptt, recorder, clock, delivered = make_ptt()
    ptt.press()
    clock.now = 0.1
    ptt.release()
    assert delivered == [] and recorder.stops == 1


def test_repeated_press_is_ignored() -> None:
    ptt, recorder, _, _ = make_ptt()
    ptt.press()
    ptt.press()
    assert recorder.starts == 1


def test_release_without_press_is_ignored() -> None:
    ptt, recorder, _, delivered = make_ptt()
    ptt.release()
    assert recorder.stops == 0 and delivered == []
