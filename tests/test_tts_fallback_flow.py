import asyncio

import pytest

from friday.tts import RETRY_ATTEMPTS, speak_async, synthesize_with_fallback
from friday.tts_fallback import LocalTtsError


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr("friday.tts.RETRY_DELAY", 0)


class Edge:
    def __init__(self, text, voice, rate, pitch):
        self.text = text

    async def stream(self):
        if "fail" not in self.text:
            yield {"type": "audio", "data": self.text.encode()}


def local_voice(text: str) -> bytes:
    return b"LOCAL:" + text.encode()


def test_edge_is_tried_twice_by_default() -> None:
    assert RETRY_ATTEMPTS == 2


def test_local_voice_is_not_used_when_edge_works() -> None:
    used = []
    audio = asyncio.run(
        synthesize_with_fallback(
            "Раз", communicate=Edge, local=lambda t: used.append(t) or b"x"
        )
    )
    assert audio == "Раз".encode() and used == []


def test_local_voice_takes_over_when_edge_fails() -> None:
    audio = asyncio.run(
        synthesize_with_fallback("fail", communicate=Edge, local=local_voice)
    )
    assert audio == "LOCAL:fail".encode()


def test_without_a_local_voice_the_error_stays() -> None:
    with pytest.raises(Exception):
        asyncio.run(synthesize_with_fallback("fail", communicate=Edge))


def test_speak_voices_the_failed_piece_in_place() -> None:
    played = []
    count = asyncio.run(
        speak_async(
            "Раз. fail. Три.", played.append, communicate=Edge, local=local_voice
        )
    )
    assert count == 3
    assert played == ["Раз.".encode(), b"LOCAL:fail.", "Три.".encode()]


def test_speak_skips_a_piece_when_the_local_voice_fails_too() -> None:
    def broken(text: str) -> bytes:
        raise LocalTtsError("no voice")

    played = []
    count = asyncio.run(
        speak_async("Раз. fail. Три.", played.append, communicate=Edge, local=broken)
    )
    assert count == 2
    assert played == ["Раз.".encode(), "Три.".encode()]
