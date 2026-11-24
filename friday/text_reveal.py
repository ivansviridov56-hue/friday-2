"""Pure logic for showing the answer on the island in step with her voice."""

from __future__ import annotations

import math


def chunk_spans(text: str, chunks: list[str]) -> list[tuple[int, int]]:
    """Where each spoken chunk sits in `text`, as (start, end), in order.

    The chunks are cut from the same cleaned text, so a forward search finds them.
    A chunk that cannot be found takes the next stretch of the text by its length.
    """
    spans: list[tuple[int, int]] = []
    pos = 0
    for chunk in chunks:
        found = text.find(chunk, pos)
        start = found if found != -1 else min(pos, len(text))
        end = min(start + len(chunk), len(text))
        spans.append((start, end))
        pos = end
    return spans


def progress_at(elapsed: float, duration: float) -> float:
    """Share of a chunk already spoken, 0..1. A chunk with no duration counts as done."""
    if duration <= 0:
        return 1.0
    return min(max(elapsed / duration, 0.0), 1.0)


def reveal_end(text: str, start: int, end: int, progress: float) -> int:
    """How many characters of `text` are shown while a chunk (start, end) is spoken.

    A word appears as soon as the speech reaches it and is never cut in the middle.
    Progress 0 shows nothing of the chunk, progress 1 shows all of it.
    """
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))
    if end == start or progress <= 0:
        return start
    if progress >= 1:
        return end
    index = start + int((end - start) * progress)
    if index >= end:
        return end
    if text[index].isspace():
        return index
    stop = index
    while stop < end and not text[stop].isspace():
        stop += 1
    return stop


def scroll_target(shown_lines: int, max_lines: int) -> int:
    """How many lines to scroll up so the last `max_lines` shown lines stay visible."""
    if max_lines <= 0:
        raise ValueError("max_lines must be positive")
    return max(0, shown_lines - max_lines)


def ease_toward(current: float, target: float, dt: float, rate: float) -> float:
    """Move `current` toward `target`; the result does not depend on the frame rate."""
    if dt <= 0 or rate <= 0:
        return current
    return target + (current - target) * math.exp(-rate * dt)


def locate_chunk(text: str, chunk: str, pos: int = 0) -> tuple[int, int] | None:
    """Where `chunk` sits in `text` at or after `pos`, as (start, end); None if it is not there.

    Unlike chunk_spans, a missing chunk is not guessed: a phrase that is not part of the
    answer (for example the announcement before a screen description) must not move the reveal.
    """
    if not chunk:
        return None
    start = text.find(chunk, max(pos, 0))
    if start == -1:
        return None
    return (start, start + len(chunk))
