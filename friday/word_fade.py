"""Pure logic for words that fade in on the island (stage 27e). No Qt here.

A span is (start, end, born): a stretch of the text that appeared at time `born`.
Its colour goes from the body colour to the text colour in FADE_SECONDS.
"""

from __future__ import annotations

import html
from typing import Callable

Span = tuple[int, int, float]

FADE_SECONDS = 0.25


def fade_alpha(age: float, seconds: float = FADE_SECONDS) -> float:
    """How far a word has faded in, 0..1 (smooth start and end)."""
    if seconds <= 0:
        return 1.0
    t = min(max(age / seconds, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def add_span(spans: list[Span], start: int, end: int, born: float) -> list[Span]:
    """A new list with one more span; an empty span is ignored."""
    if end <= start:
        return list(spans)
    return [*spans, (start, end, born)]


def live_spans(
    spans: list[Span], now: float, seconds: float = FADE_SECONDS
) -> list[Span]:
    """Only the spans that are still fading."""
    return [s for s in spans if now - s[2] < seconds]


def _escape(piece: str) -> str:
    return html.escape(piece, quote=False).replace("\n", "<br>")


def build_markup(
    text: str,
    spans: list[Span],
    now: float,
    color_at: Callable[[float], str],
    seconds: float = FADE_SECONDS,
) -> str:
    """StyledText: the plain text, with fading spans in a colour from color_at(alpha)."""
    parts: list[str] = []
    pos = 0
    for start, end, born in sorted(live_spans(spans, now, seconds)):
        start = max(start, pos)
        end = min(end, len(text))
        if end <= start:
            continue
        if start > pos:
            parts.append(_escape(text[pos:start]))
        colour = color_at(fade_alpha(now - born, seconds))
        parts.append(f'<font color="{colour}">{_escape(text[start:end])}</font>')
        pos = end
    if pos < len(text):
        parts.append(_escape(text[pos:]))
    return "".join(parts)
