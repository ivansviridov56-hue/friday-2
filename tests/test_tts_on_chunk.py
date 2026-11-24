import asyncio
import io
import wave

import pytest

from friday.tts import speak_async

TEXT = "Hello there. How are you doing today?"


def make_wav(seconds: float, rate: int = 48000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(b"\x00\x00" * int(seconds * rate))
    return buffer.getvalue()


def run(**kwargs):
    return asyncio.run(speak_async(TEXT, **kwargs))


def test_on_chunk_is_called_before_each_piece_plays():
    events = []
    run(
        play=lambda audio: events.append("play"),
        engine=lambda chunk: make_wav(1.5),
        on_chunk=lambda text, seconds: events.append(("chunk", text, seconds)),
    )
    assert events[0] == ("chunk", "Hello there.", pytest.approx(1.5))
    assert events[1] == "play"
    assert events[2] == ("chunk", "How are you doing today?", pytest.approx(1.5))
    assert events[3] == "play"


def test_on_chunk_skips_a_piece_that_failed_to_voice():
    heard = []

    def engine(chunk: str) -> bytes:
        if "How" in chunk:
            raise RuntimeError("no audio")
        return make_wav(1.0)

    played = run(
        play=lambda audio: None,
        engine=engine,
        on_chunk=lambda text, seconds: heard.append(text),
    )
    assert played == 1
    assert heard == ["Hello there."]


def test_a_broken_on_chunk_does_not_stop_the_speech():
    def broken(text: str, seconds: float) -> None:
        raise RuntimeError("boom")

    played = run(
        play=lambda audio: None, engine=lambda chunk: make_wav(1.0), on_chunk=broken
    )
    assert played == 2


def test_speech_works_without_on_chunk():
    played = run(play=lambda audio: None, engine=lambda chunk: make_wav(1.0))
    assert played == 2
