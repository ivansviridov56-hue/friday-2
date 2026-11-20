"""Tests for the Silero voice wrapper (no torch needed: the model is faked)."""

import io
import struct
import wave

import pytest

from friday.tts_silero import SileroError, SileroVoice, samples_to_wav


class FakeAudio:
    """Stands in for a torch tensor: only tolist() is used."""

    def __init__(self, samples):
        self._samples = list(samples)

    def tolist(self):
        return list(self._samples)


class FakeModel:
    def __init__(self, samples=(0.0, 0.5, -0.5, 1.0), fail=False):
        self.samples = samples
        self.fail = fail
        self.calls = []

    def apply_tts(self, text, speaker, sample_rate):
        self.calls.append((text, speaker, sample_rate))
        if self.fail:
            raise RuntimeError("boom")
        return FakeAudio(self.samples)


def read_wav(data: bytes):
    with wave.open(io.BytesIO(data), "rb") as wav:
        frames = wav.readframes(wav.getnframes())
        return (
            wav.getnchannels(),
            wav.getsampwidth(),
            wav.getframerate(),
            struct.unpack(f"<{wav.getnframes()}h", frames),
        )


def test_samples_to_wav_is_mono_16bit_with_given_rate():
    channels, width, rate, values = read_wav(
        samples_to_wav([0.0, 0.5, -0.5, 1.0], 24000)
    )
    assert (channels, width, rate) == (1, 2, 24000)
    assert values == (0, 16383, -16383, 32767)


def test_samples_to_wav_clips_out_of_range_values():
    *_, values = read_wav(samples_to_wav([2.0, -2.0], 24000))
    assert values == (32767, -32767)


def test_model_is_not_loaded_on_creation():
    loads = []
    SileroVoice(loader=lambda: loads.append(1) or FakeModel())
    assert loads == []


def test_model_is_loaded_once_for_many_phrases():
    loads = []

    def loader():
        loads.append(1)
        return FakeModel()

    voice = SileroVoice(loader=loader)
    voice.synthesize("Привет.")
    voice.synthesize("Пока.")
    assert len(loads) == 1


def test_warm_up_loads_the_model():
    loads = []
    voice = SileroVoice(loader=lambda: loads.append(1) or FakeModel())
    voice.warm_up()
    assert len(loads) == 1


def test_synthesize_passes_text_speaker_and_rate_to_the_model():
    model = FakeModel()
    voice = SileroVoice(speaker="kseniya", sample_rate=24000, loader=lambda: model)
    data = voice.synthesize("Привет.")
    assert model.calls == [("Привет.", "kseniya", 24000)]
    assert read_wav(data)[2] == 24000


def test_default_voice_is_kseniya():
    model = FakeModel()
    SileroVoice(loader=lambda: model).synthesize("Привет.")
    assert model.calls[0][1] == "kseniya"


def test_empty_text_is_an_error():
    voice = SileroVoice(loader=lambda: FakeModel())
    with pytest.raises(SileroError):
        voice.synthesize("   ")


def test_loader_failure_is_an_error_and_is_retried_next_time():
    attempts = []

    def loader():
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("no network")
        return FakeModel()

    voice = SileroVoice(loader=loader)
    with pytest.raises(SileroError):
        voice.synthesize("Привет.")
    voice.synthesize("Привет.")
    assert len(attempts) == 2


def test_model_failure_is_an_error():
    voice = SileroVoice(loader=lambda: FakeModel(fail=True))
    with pytest.raises(SileroError):
        voice.synthesize("Привет.")
