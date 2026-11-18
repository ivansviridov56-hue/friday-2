import numpy as np
import pytest

from friday.wake_probe import Attempt, heard_name, record_clip, summarize


class FakeRecorder:
    def __init__(self) -> None:
        self.events: list[str] = []

    def start(self) -> None:
        self.events.append("start")

    def stop(self) -> np.ndarray:
        self.events.append("stop")
        return np.ones(3, dtype=np.float32)


@pytest.mark.parametrize(
    "text",
    [
        "Пятница",
        "пятница!",
        "Слушай, Пятница, включи музыку",
        "Пятницу",
        "ПЯТНИЦА",
    ],
)
def test_name_is_found(text: str) -> None:
    assert heard_name(text) is True


@pytest.mark.parametrize(
    "text",
    ["Бэтни", "Пятый", "", "Сижу в пятом ряду", "пят ница"],
)
def test_name_is_not_found(text: str) -> None:
    assert heard_name(text) is False


def test_record_clip_records_for_the_given_time() -> None:
    recorder = FakeRecorder()
    audio = record_clip(
        recorder, 3, sleep=lambda s: recorder.events.append(f"sleep:{s}")
    )
    assert recorder.events == ["start", "sleep:3", "stop"]
    assert audio.size == 3


def test_record_clip_stops_even_when_interrupted() -> None:
    recorder = FakeRecorder()

    def sleep(_: float) -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        record_clip(recorder, 3, sleep=sleep)
    assert recorder.events == ["start", "stop"]


def test_summary_of_nothing() -> None:
    assert summarize([]) == "no clips"


def test_summary_all_found() -> None:
    attempts = [Attempt("a", "Пятница"), Attempt("b", "Эй, пятница")]
    assert summarize(attempts) == "name found in 2 of 2 clips"


def test_summary_lists_misses() -> None:
    attempts = [Attempt("quiet", "Бэтни"), Attempt("loud", "Пятница!")]
    text = summarize(attempts)
    assert text.startswith("name found in 1 of 2 clips")
    assert "missed [quiet]: 'Бэтни'" in text
    assert "loud" not in text
