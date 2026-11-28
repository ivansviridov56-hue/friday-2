"""Outline of the island as lists of points (pure geometry, no Qt).

The window only draws these points; the rules of the shape live here, so tests can check them.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from friday.island_logic import edge_gap, wave_offset
from friday.island_eq import eq_offset

FLARE = 10  # the concave curve that joins the island to the top edge of the screen
RADIUS = 14  # rounding of the bottom corners
ARC_STEPS = 6
FLARE_STEPS = 6
WAVE_STEP = 3  # px between the points of the wavy edge
WAVE_LAG = 0.5  # the light line follows the edge a little later (radians)

Point = tuple[float, float]


def _check(window_w: float, body_w: float) -> None:
    if body_w <= 2 * RADIUS:
        raise ValueError("the body must be wider than its two corners")
    if window_w < body_w + 2 * FLARE:
        raise ValueError("the window must fit the body and both flares")


def _bezier(p0: Point, p1: Point, p2: Point, steps: int) -> list[Point]:
    points = []
    for i in range(steps + 1):
        t = i / steps
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        points.append(
            (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])
        )
    return points


def _edge_segments(edge_w: float) -> int:
    n = max(2, math.ceil(edge_w / WAVE_STEP))
    return n + (n % 2)  # an even count keeps the middle point and the symmetry


def _edge_shift(
    u: float,
    edge_w: float,
    phase: float,
    amplitude: float,
    spatial: float,
    eq: Sequence[float],
    eq_mix: float,
) -> float:
    """Shift of the bottom edge: the wave, blended into the equalizer by eq_mix (0..1)."""
    wave = wave_offset(u, edge_w, phase, amplitude, spatial)
    if eq_mix <= 0 or not eq:
        return wave
    return wave + (eq_offset(u, edge_w, eq) - wave) * min(eq_mix, 1.0)


def body_outline(
    window_w: float,
    body_w: float,
    body_h: float,
    amplitude: float,
    spatial: float,
    phase: float,
    eq: Sequence[float] = (),
    eq_mix: float = 0.0,
) -> list[Point]:
    """Closed outline of the island body, from the left flare round to the right flare."""
    _check(window_w, body_w)
    x0 = (window_w - (body_w + 2 * FLARE)) / 2
    left = x0 + FLARE
    right = left + body_w
    corner_y = body_h - RADIUS
    edge_x0, edge_w = left + RADIUS, body_w - 2 * RADIUS

    points = _bezier((x0, 0.0), (left, 0.0), (left, float(FLARE)), FLARE_STEPS)
    for k in range(ARC_STEPS + 1):
        a = math.pi - (math.pi / 2) * k / ARC_STEPS
        points.append((edge_x0 + RADIUS * math.cos(a), corner_y + RADIUS * math.sin(a)))
    n = _edge_segments(edge_w)
    for i in range(1, n):
        u = edge_w * i / n
        shift = _edge_shift(u, edge_w, phase, amplitude, spatial, eq, eq_mix)
        points.append((edge_x0 + u, body_h + shift))
    for m in range(ARC_STEPS + 1):
        b = (math.pi / 2) - (math.pi / 2) * m / ARC_STEPS
        points.append(
            (right - RADIUS + RADIUS * math.cos(b), corner_y + RADIUS * math.sin(b))
        )
    points += _bezier(
        (right, float(FLARE)), (right, 0.0), (right + FLARE, 0.0), FLARE_STEPS
    )
    return points


def light_line(
    window_w: float,
    body_w: float,
    body_h: float,
    amplitude: float,
    spatial: float,
    phase: float,
    eq: Sequence[float] = (),
    eq_mix: float = 0.0,
) -> list[Point]:
    """The thin light line under the wavy edge, a little later in phase and above the edge."""
    _check(window_w, body_w)
    left = (window_w - (body_w + 2 * FLARE)) / 2 + FLARE
    edge_x0, edge_w = left + RADIUS, body_w - 2 * RADIUS
    n = _edge_segments(edge_w)
    points = []
    for i in range(n + 1):
        u = edge_w * i / n
        shift = _edge_shift(u, edge_w, phase - WAVE_LAG, amplitude, spatial, eq, eq_mix)
        points.append((edge_x0 + u, body_h + shift - edge_gap(u, edge_w)))
    return points
