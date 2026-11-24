"""Glue between the voice and the event bus: which piece of the answer sounds now."""

from __future__ import annotations

from collections.abc import Callable

from friday.ui_events import SpeechChunkStarted, UiEventBus


def make_chunk_publisher(bus: UiEventBus) -> Callable[[str, float], None]:
    def publish(text: str, seconds: float) -> None:
        bus.publish(SpeechChunkStarted(text, seconds))

    return publish
