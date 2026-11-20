import logging

import numpy as np

from friday.speech_segmenter import EndInfo
from friday.wake_listener import WakeListener


class Mic:
    def add_listener(self, listener) -> None: ...

    def remove_listener(self, listener) -> None: ...


class Stt:
    def transcribe(self, audio: np.ndarray) -> str:
        return "просто разговор"  # no name: nothing is submitted


class FakeCutter:
    in_speech = False

    def __init__(self, last_end=None) -> None:
        if last_end is not None:
            self.last_end = last_end

    def feed(self, samples):
        return [np.zeros(16000 * 12, dtype=np.float32)]

    def reset(self) -> None: ...


def make(cutter) -> WakeListener:
    return WakeListener(
        Mic(), Stt(), lambda text: True, lambda: False, segmenter=cutter
    )


def test_log_shows_why_the_phrase_ended(caplog) -> None:
    listener = make(FakeCutter(EndInfo("max", 0.004, 0.0011)))
    with caplog.at_level(logging.INFO):
        listener.process(np.zeros(480, dtype=np.float32))
    line = next(r.getMessage() for r in caplog.records if "phrase" in r.getMessage())
    assert "ended=max" in line
    assert "thr=0.0040" in line
    assert "floor=0.0011" in line


def test_a_cutter_without_end_info_still_works(caplog) -> None:
    listener = make(FakeCutter())  # like the older fakes in the existing tests
    with caplog.at_level(logging.INFO):
        listener.process(np.zeros(480, dtype=np.float32))
    line = next(r.getMessage() for r in caplog.records if "phrase" in r.getMessage())
    assert "ended=" not in line


def test_phrase_text_is_still_not_logged(caplog) -> None:
    listener = make(FakeCutter(EndInfo("silence", 0.004, 0.001)))
    with caplog.at_level(logging.INFO):
        listener.process(np.zeros(480, dtype=np.float32))
    assert "разговор" not in caplog.text
