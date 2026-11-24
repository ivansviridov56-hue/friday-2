"""Text-to-speech: Edge TTS synthesis, sentence by sentence, with prefetching."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass

from friday.tts_fallback import synthesize_local
from friday.audio_duration import audio_seconds

log = logging.getLogger(__name__)

_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+")
_MARKDOWN = re.compile(r"[*_#`~>]")
_CLAUSE_BREAK = re.compile(r"(?<=[,;:])\s+")
FIRST_CHUNK_MAX = 50
CHUNK_MAX = 90
MAX_PARALLEL = 2
RETRY_ATTEMPTS = (
    1  # a failed Edge try costs seconds and rarely recovers: go local at once
)
RETRY_DELAY = 0.4  # seconds, multiplied by the attempt number


class TtsError(Exception):
    pass


@dataclass(frozen=True)
class TtsSettings:
    voice: str = "ru-RU-SvetlanaNeural"
    rate: str = "+30%"
    pitch: str = "+0Hz"


def clean_for_speech(text: str) -> str:
    """Remove markdown symbols the voice would stumble on."""
    return " ".join(_MARKDOWN.sub("", text).split())


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_BREAK.split(text) if part.strip()]


def split_for_speech(
    text: str, first_max: int = FIRST_CHUNK_MAX, max_len: int = CHUNK_MAX
) -> list[str]:
    """Sentences, with long ones cut at commas so the first sound starts sooner."""
    chunks: list[str] = []
    for sentence in split_sentences(text):
        limit = first_max if not chunks else max_len
        if len(sentence) <= limit:
            chunks.append(sentence)
            continue
        current = ""
        for piece in _CLAUSE_BREAK.split(sentence):
            limit = first_max if not chunks else max_len
            candidate = f"{current} {piece}".strip()
            if current and len(candidate) > limit:
                chunks.append(current)
                current = piece
            else:
                current = candidate
        if current:
            chunks.append(current)
    return chunks


async def synthesize(
    text: str, settings: TtsSettings = TtsSettings(), communicate=None
) -> bytes:
    """Return mp3 bytes for one piece of text."""
    if communicate is None:
        import edge_tts

        communicate = edge_tts.Communicate
    started = time.perf_counter()
    speaker = communicate(
        text, settings.voice, rate=settings.rate, pitch=settings.pitch
    )
    chunks = []
    async for chunk in speaker.stream():
        if chunk["type"] == "audio":
            data = chunk.get("data")
            if data:
                chunks.append(data)
    if not chunks:
        raise TtsError("no audio received")
    log.info(
        "synthesized %d chars in %d ms",
        len(text),
        int((time.perf_counter() - started) * 1000),
    )
    return b"".join(chunks)


async def synthesize_with_retry(
    text: str,
    settings: TtsSettings = TtsSettings(),
    communicate=None,
    attempts: int = RETRY_ATTEMPTS,
) -> bytes:
    """Edge sometimes answers with no audio; a short pause and retry fixes most."""
    for attempt in range(1, attempts + 1):
        try:
            return await synthesize(text, settings, communicate)
        except Exception as exc:
            if attempt == attempts:
                raise
            log.warning(
                "tts attempt %d/%d failed for %r: %s",
                attempt,
                attempts,
                text[:30],
                type(exc).__name__,
            )
            await asyncio.sleep(RETRY_DELAY * attempt)
    raise TtsError("unreachable")  # keeps type checkers happy


async def synthesize_with_fallback(
    text: str,
    settings: TtsSettings = TtsSettings(),
    communicate=None,
    local: Callable[[str], bytes] | None = None,
) -> bytes:
    """Edge first; if it cannot voice the text, the local voice does (when given)."""
    try:
        return await synthesize_with_retry(
            text, settings, communicate, attempts=RETRY_ATTEMPTS
        )
    except Exception as exc:
        if local is None:
            raise
        log.warning(
            "tts: Edge failed for %r (%s), using the local voice",
            text[:30],
            type(exc).__name__,
        )
    return await asyncio.to_thread(local, text)


async def speak_async(
    text: str,
    play,
    settings: TtsSettings = TtsSettings(),
    communicate=None,
    local: Callable[[str], bytes] | None = None,
    engine: Callable[[str], bytes] | None = None,
    on_chunk: Callable[[str, float], None] | None = None,
) -> int:
    """Speak `text` piece by piece. Returns how many pieces were played.

    `on_chunk(text, seconds)` is called just before a piece starts to sound.

    With `engine` (e.g. Silero) every piece is voiced by it and Edge is not used.
    """
    chunks = split_for_speech(clean_for_speech(text))
    gate = asyncio.Semaphore(MAX_PARALLEL)

    async def render(chunk: str) -> bytes:
        async with gate:
            if engine is not None:
                return await asyncio.to_thread(engine, chunk)
            return await synthesize_with_fallback(chunk, settings, communicate, local)

    begun = time.perf_counter()
    tasks = [asyncio.create_task(render(chunk)) for chunk in chunks]
    played = 0
    try:
        for index, (chunk, task) in enumerate(zip(chunks, tasks), start=1):
            try:
                audio = await task
            except Exception as exc:  # one bad piece must not silence the rest
                log.warning("tts failed for %r: %s", chunk[:30], type(exc).__name__)
                continue
            log.info(
                "chunk %d/%d ready at %d ms",
                index,
                len(chunks),
                int((time.perf_counter() - begun) * 1000),
            )
            _announce(on_chunk, chunk, audio)
            await asyncio.to_thread(play, audio)
            played += 1
    finally:
        for task in tasks:
            task.cancel()
    return played


def _announce(on_chunk, chunk: str, audio: bytes) -> None:
    """Tell the outside which piece sounds now; a broken callback never stops the speech."""
    if on_chunk is None:
        return
    try:
        on_chunk(chunk, audio_seconds(audio, chunk))
    except Exception:
        log.exception("on_chunk failed")


def speak_text(
    text: str,
    play,
    settings: TtsSettings = TtsSettings(),
    engine: Callable[[str], bytes] | None = None,
    on_chunk: Callable[[str, float], None] | None = None,
) -> int:
    return asyncio.run(
        speak_async(
            text,
            play,
            settings,
            local=synthesize_local,
            engine=engine,
            on_chunk=on_chunk,
        )
    )
