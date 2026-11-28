"""Equalizer shape of the island's bottom edge. Pure logic: no Qt, no audio."""

from __future__ import annotations

import math
from collections.abc import Sequence

from friday.island_logic import smoothstep

EQ_AMPLITUDE = 6.0  # px, how far the edge goes down at the full level
EQ_EDGE = 0.1  # share of the edge width at each end where the bars fade to zero


def eq_value(u: float, levels: Sequence[float]) -> float:
    """Level (0..1) at position u (0..1) across the edge, smooth between band centres."""
    count = len(levels)
    if count == 0:
        return 0.0
    if count == 1:
        return levels[0]
    pos = min(max(u, 0.0), 1.0) * count - 0.5  # band centres sit at 0, 1, 2, ...
    if pos <= 0:
        return levels[0]
    if pos >= count - 1:
        return levels[-1]
    i = int(pos)
    t = (1 - math.cos(math.pi * (pos - i))) / 2
    return levels[i] + (levels[i + 1] - levels[i]) * t


def eq_offset(
    x: float, width: float, levels: Sequence[float], amplitude: float = EQ_AMPLITUDE
) -> float:
    """Vertical shift (px, positive = down) of the bottom edge at x in 0..width.

    Fades to zero at both ends, so the edge joins the rounded corners smoothly.
    """
    if width <= 0:
        raise ValueError("width must be positive")
    u = min(max(x / width, 0.0), 1.0)
    taper = smoothstep(u / EQ_EDGE) * smoothstep((1 - u) / EQ_EDGE)
    level = min(max(eq_value(u, levels), 0.0), 1.0)
    return amplitude * taper * level
