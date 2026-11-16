from dataclasses import dataclass

import numpy as np

from friday.stt import SpeechToText


@dataclass
class FakeSegment:
    text: str


class FakeModel:
    def __init__(self, texts: list[str]) -> None:
        self.texts = texts
        self.calls: list[dict] = []

    def transcribe(self, audio, **kwargs):
        self.calls.append({"audio": audio, **kwargs})
        return iter([FakeSegment(t) for t in self.texts]), object()


def make_stt(texts: list[str]) -> tuple[SpeechToText, FakeModel, list[int]]:
    model = FakeModel(texts)
    created: list[int] = []

    def factory(name: str, device: str, compute_type: str) -> FakeModel:
        created.append(1)
        return model

    return SpeechToText(model_factory=factory), model, created


def test_joins_and_strips_segments() -> None:
    stt, _, _ = make_stt([" Привет, ", "  как дела? "])
    assert stt.transcribe(np.ones(16000, dtype=np.float32)) == "Привет, как дела?"


def test_empty_audio_returns_empty_without_model() -> None:
    stt, model, created = make_stt(["x"])
    assert stt.transcribe(np.zeros(0, dtype=np.float32)) == ""
    assert model.calls == [] and created == []


def test_converts_audio_to_float32_and_uses_russian_with_vad() -> None:
    stt, model, _ = make_stt(["ок"])
    stt.transcribe(np.ones(16000, dtype=np.float64))
    call = model.calls[0]
    assert call["audio"].dtype == np.float32
    assert call["language"] == "ru"
    assert call["vad_filter"] is True


def test_model_is_created_once() -> None:
    stt, _, created = make_stt(["ок"])
    stt.transcribe(np.ones(16000, dtype=np.float32))
    stt.transcribe(np.ones(16000, dtype=np.float32))
    assert len(created) == 1


def test_warm_up_async_marks_ready() -> None:
    stt, model, _ = make_stt([])
    assert not stt.is_ready
    stt.warm_up_async().join(timeout=5)
    assert stt.is_ready
    assert len(model.calls) == 1  # one silent run
