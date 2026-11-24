import io
import wave

import pytest

from friday.audio_duration import (
    MIN_SECONDS,
    audio_seconds,
    estimate_seconds,
    wav_seconds,
)


def make_wav(seconds: float, rate: int = 48000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(b"\x00\x00" * int(seconds * rate))
    return buffer.getvalue()


def test_wav_seconds_reads_exact_length():
    assert wav_seconds(make_wav(1.0)) == pytest.approx(1.0)


def test_wav_seconds_uses_the_sample_rate():
    assert wav_seconds(make_wav(2.5, rate=24000)) == pytest.approx(2.5)


def test_wav_seconds_none_for_mp3():
    assert wav_seconds(b"ID3\x04\x00\x00" + b"\x00" * 50) is None


def test_wav_seconds_none_for_broken_wav():
    assert wav_seconds(b"RIFFxxxxWAVE") is None


def test_estimate_grows_with_text():
    assert estimate_seconds("a" * 60) > estimate_seconds("a" * 30)


def test_estimate_has_a_minimum():
    assert estimate_seconds("") == MIN_SECONDS


def test_audio_seconds_prefers_the_wav_length():
    assert audio_seconds(make_wav(3.0), "short") == pytest.approx(3.0)


def test_audio_seconds_estimates_for_mp3():
    text = "a" * 45
    assert audio_seconds(b"ID3\x04\x00", text) == estimate_seconds(text)


def test_audio_seconds_estimates_for_empty_wav():
    text = "hello there"
    assert audio_seconds(make_wav(0.0), text) == estimate_seconds(text)
