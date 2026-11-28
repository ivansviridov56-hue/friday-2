"""Equalizer levels on the island's stdin line: "eq 0 12 100 ..." (integers 0..100)."""

from __future__ import annotations

import math
from collections.abc import Iterable

EQ_BANDS = 16
EQ_SCALE = 100


def format_eq(levels: Iterable[float]) -> str:
    """Levels 0..1 -> the text after "eq "; out-of-range values are clamped, NaN is 0."""
    parts = []
    for level in levels:
        number = float(level)
        if not math.isfinite(number):
            number = 0.0
        parts.append(str(round(min(max(number, 0.0), 1.0) * EQ_SCALE)))
    return " ".join(parts)


def parse_eq(arg: str, bands: int = EQ_BANDS) -> list[float] | None:
    """The text after "eq " -> levels 0..1; None for anything that is not a full valid line."""
    parts = arg.split()
    if len(parts) != bands:
        return None
    levels = []
    for part in parts:
        try:
            value = int(part)
        except ValueError:
            return None
        if not 0 <= value <= EQ_SCALE:
            return None
        levels.append(value / EQ_SCALE)
    return levels
