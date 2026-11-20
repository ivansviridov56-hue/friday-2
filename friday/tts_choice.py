"""Pick the voice engine by name (TTS_ENGINE in .env): Silero by default, or Edge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TtsChoice:
    """`engine` is None for Edge (friday.tts then uses its own Edge path)."""

    engine: Callable[[str], bytes] | None
    warm_up: Callable[[], None]


def _default_silero_factory() -> Any:
    from friday.tts_silero import SileroVoice

    return SileroVoice()


def choose_tts(
    name: str | None, silero_factory: Callable[[], Any] = _default_silero_factory
) -> TtsChoice:
    normalized = (name or "").strip().lower() or "silero"
    if normalized == "edge":
        return TtsChoice(engine=None, warm_up=lambda: None)
    if normalized == "silero":
        voice = silero_factory()
        return TtsChoice(engine=voice.synthesize, warm_up=voice.warm_up)
    raise ValueError(f"unknown TTS_ENGINE {name!r}: use 'silero' or 'edge'")
