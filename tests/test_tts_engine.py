"""speak_async with a custom engine (Silero): Edge must stay untouched."""

import asyncio

from friday.tts import speak_async


class ForbiddenEdge:
    """Stands in for edge_tts.Communicate: any use is a test failure."""

    def __init__(self, *args, **kwargs):
        raise AssertionError("Edge must not be used when an engine is given")


def fake_engine(text: str) -> bytes:
    return b"RIFF" + text.encode()


def test_engine_voices_every_chunk_in_order_without_edge():
    played = []
    count = asyncio.run(
        speak_async(
            "Первая фраза. Вторая фраза.",
            played.append,
            communicate=ForbiddenEdge,
            engine=fake_engine,
        )
    )
    assert count == 2
    assert played == [
        b"RIFF" + "Первая фраза.".encode(),
        b"RIFF" + "Вторая фраза.".encode(),
    ]


def test_markdown_is_cleaned_before_the_engine_gets_the_text():
    seen = []

    def engine(text: str) -> bytes:
        seen.append(text)
        return b"RIFF"

    asyncio.run(speak_async("**Привет**.", lambda audio: None, engine=engine))
    assert seen == ["Привет."]


def test_one_failed_chunk_does_not_silence_the_rest():
    played = []

    def engine(text: str) -> bytes:
        if text.startswith("Плохо"):
            raise RuntimeError("boom")
        return b"RIFF" + text.encode()

    count = asyncio.run(
        speak_async("Хорошо. Плохо. Снова хорошо.", played.append, engine=engine)
    )
    assert count == 2
    assert len(played) == 2
