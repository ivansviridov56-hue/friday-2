"""Length of one spoken piece, so the island can show text in step with the voice."""

from __future__ import annotations

import io
import wave

# Rough speed of the Edge voice at +30 %; used only when the exact length is unknown (mp3).
CHARS_PER_SECOND = 15.0
MIN_SECONDS = 0.3


def estimate_seconds(text: str) -> float:
    return max(MIN_SECONDS, len(text) / CHARS_PER_SECOND)


def wav_seconds(audio: bytes) -> float | None:
    """Exact length of PCM WAV bytes, or None if they are not a readable WAV."""
    if not audio.startswith(b"RIFF"):
        return None
    try:
        with wave.open(io.BytesIO(audio), "rb") as reader:
            rate = reader.getframerate()
            if rate <= 0:
                return None
            return reader.getnframes() / rate
    except (wave.Error, EOFError):
        return None


def audio_seconds(audio: bytes, text: str) -> float:
    """WAV (Silero, Irina): exact length from the bytes. Otherwise an estimate from the text."""
    exact = wav_seconds(audio)
    if exact is not None and exact > 0:
        return exact
    return estimate_seconds(text)
