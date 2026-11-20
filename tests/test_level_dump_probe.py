import numpy as np
import pytest

from friday.level_dump_probe import (
    Mark,
    Step,
    format_dump,
    parse_dump,
    record_steps,
)
from friday.speech_segmenter import SAMPLE_RATE
from collections.abc import Callable


def test_dump_roundtrip() -> None:
    levels = np.array([0.0, 0.0123456, 0.5], dtype=np.float32)
    marks = [Mark(0.0, "music"), Mark(1.5, "speak")]
    got_levels, got_marks, frame_ms = parse_dump(format_dump(levels, marks, 30))
    assert frame_ms == 30
    assert got_marks == marks
    assert np.allclose(got_levels, levels, atol=1e-6)


def test_dump_has_only_numbers_and_labels() -> None:
    text = format_dump(np.array([0.1, 0.2], dtype=np.float32), [Mark(0.0, "a")], 30)
    for line in text.splitlines():
        assert line.startswith("#") or line.replace(".", "", 1).isdigit()


def test_label_with_spaces_is_rejected() -> None:
    with pytest.raises(ValueError):
        format_dump(np.zeros(1, dtype=np.float32), [Mark(0.0, "two words")], 30)


def test_empty_levels_are_rejected() -> None:
    with pytest.raises(ValueError):
        format_dump(np.zeros(0, dtype=np.float32), [], 30)


def test_parse_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_dump("hello")


class FakeRecorder:
    def __init__(self) -> None:
        self.listener: Callable[[np.ndarray], object] | None = None
        self.removed = False

    def add_listener(self, listener) -> None:
        self.listener = listener

    def remove_listener(self, listener) -> None:
        self.removed = listener is self.listener


def test_record_steps_marks_follow_the_audio() -> None:
    rec = FakeRecorder()

    def sleep(seconds: float) -> None:  # the "microphone" delivers audio meanwhile
        assert rec.listener is not None
        rec.listener(np.full(int(SAMPLE_RATE * seconds), 0.01, dtype=np.float32))

    steps = [Step("music", "молчи", 2.0), Step("speak", "говори", 1.0)]
    said: list[str] = []
    audio, marks = record_steps(rec, steps, sleep=sleep, say=said.append)
    assert audio.size == 3 * SAMPLE_RATE
    assert marks == [Mark(0.0, "music"), Mark(2.0, "speak")]
    assert said == ["молчи", "говори"]
    assert rec.removed
