"""Looks of the island icon (stage 29a): pure logic, no Qt.

A look turns (state, time) into a list of rounded rectangles drawn around the centre of the
icon. A shape is (cx, cy, w, h, radius) in pixels, relative to that centre. A new look is one
function here plus its name in LOOKS; the window only draws what a look says.
"""

from __future__ import annotations

import math
from typing import Callable

Shape = tuple[float, float, float, float, float]

LOOKS = ("dot", "eyes", "equalizer", "blobs")
DEFAULT_LOOK = "dot"

# dot
DOT_RADIUS = 5.0
DOT_PULSE = 1.5

# eyes
EYE_W = 5.0
EYE_GAP = 5.5  # distance from the centre to each eye
EYE_HEIGHT = {
    "idle": 9.0,
    "listening": 11.5,
    "thinking": 8.0,
    "speaking": 9.0,
    "loading": 8.0,
    "error": 3.0,
}
EYE_HEIGHT_DEFAULT = 9.0
BLINK_PERIOD = 4.2
BLINK_SECONDS = 0.16
BLINK_DEPTH = 0.85
NO_BLINK = frozenset({"listening", "error"})
GAZE_STATES = frozenset({"thinking", "loading"})
GAZE_UP = 2.0
GAZE_SWAY = 2.0
GAZE_SECONDS = 2.4
EYE_SPEAK_GROW = 0.12

# equalizer
BARS = 4
BAR_W = 3.0
BAR_STEP = 6.0
BAR_MIN = 3.0
BAR_MAX = 14.0
BAR_LEVEL = {  # (base level, swing) per state
    "idle": (0.12, 0.06),
    "listening": (0.35, 0.40),
    "thinking": (0.30, 0.30),
    "speaking": (0.45, 0.50),
    "loading": (0.30, 0.30),
    "error": (0.05, 0.0),
}
BAR_LEVEL_DEFAULT = (0.12, 0.06)
TRAVELLING = frozenset({"thinking", "loading"})


# blobs (three soft spots drifting around the centre, like the circles look of the window)
BLOB_RADIUS = (8.0, 9.5, 7.0)
BLOB_PERIOD = (5.0, 7.0, 3.6)  # seconds per drift cycle
BLOB_PHASE = (0.0, 2.1, 4.2)
BLOB_DRIFT = {  # how far the spots wander from the centre, px
    "idle": 3.0,
    "listening": 4.5,
    "thinking": 4.0,
    "speaking": 4.0,
    "loading": 4.0,
    "error": 0.5,
}
BLOB_DRIFT_DEFAULT = 3.0
BLOB_SPEED = {  # speed factor of the drift per state
    "idle": 1.0,
    "listening": 1.6,
    "thinking": 2.6,
    "speaking": 1.8,
    "loading": 2.2,
    "error": 0.0,
}
BLOB_SCALE = {  # size factor per state
    "idle": 0.85,
    "listening": 1.0,
    "thinking": 0.9,
    "speaking": 0.95,
    "loading": 0.85,
    "error": 0.5,
}
BLOB_PULSE_GROW = 0.35


def look_or_default(name: str | None) -> str:
    """A known look name, or DEFAULT_LOOK for an empty or unknown one."""
    return name if name in LOOKS else DEFAULT_LOOK


def _dot(state: str, t: float, pulse: float) -> list[Shape]:
    r = DOT_RADIUS + DOT_PULSE * min(max(pulse, 0.0), 1.0)
    return [(0.0, 0.0, 2 * r, 2 * r, r)]


def _blink(state: str, t: float) -> float:
    """Height factor of an eye, 1 open .. 1 - BLINK_DEPTH closed."""
    if state in NO_BLINK:
        return 1.0
    phase = t % BLINK_PERIOD
    if phase >= BLINK_SECONDS:
        return 1.0
    return 1.0 - BLINK_DEPTH * math.sin(math.pi * phase / BLINK_SECONDS)


def _eyes(state: str, t: float, pulse: float) -> list[Shape]:
    h = EYE_HEIGHT.get(state, EYE_HEIGHT_DEFAULT) * _blink(state, t)
    if state == "speaking":
        h *= 1.0 + EYE_SPEAK_GROW * min(max(pulse, 0.0), 1.0)
    dx = dy = 0.0
    if state in GAZE_STATES:
        dx = GAZE_SWAY * math.sin(2 * math.pi * t / GAZE_SECONDS)
        dy = -GAZE_UP
    r = min(EYE_W, h) / 2
    return [
        (-EYE_GAP + dx, dy, EYE_W, h, r),
        (EYE_GAP + dx, dy, EYE_W, h, r),
    ]


def _bar_level(state: str, t: float, i: int) -> float:
    base, swing = BAR_LEVEL.get(state, BAR_LEVEL_DEFAULT)
    if state in TRAVELLING:
        wave = math.sin(2 * math.pi * (t / 1.1 - i / BARS))
    else:
        wave = math.sin(t * (5.0 + 1.3 * i) + 1.7 * i)
    return min(max(base + swing * (0.5 + 0.5 * wave), 0.0), 1.0)


def _equalizer(state: str, t: float, pulse: float) -> list[Shape]:
    shapes: list[Shape] = []
    for i in range(BARS):
        h = BAR_MIN + (BAR_MAX - BAR_MIN) * _bar_level(state, t, i)
        x = (i - (BARS - 1) / 2) * BAR_STEP
        shapes.append((x, 0.0, BAR_W, h, BAR_W / 2))
    return shapes


def _blobs(state: str, t: float, pulse: float) -> list[Shape]:
    speed = BLOB_SPEED.get(state, 1.0)
    drift = BLOB_DRIFT.get(state, BLOB_DRIFT_DEFAULT)
    scale = BLOB_SCALE.get(state, 1.0)
    scale *= 1.0 + BLOB_PULSE_GROW * min(max(pulse, 0.0), 1.0)
    shapes: list[Shape] = []
    for i in range(len(BLOB_RADIUS)):
        angle = 2 * math.pi * t * speed / BLOB_PERIOD[i] + BLOB_PHASE[i]
        x = drift * math.sin(angle)
        y = drift * 0.7 * math.cos(angle * 0.77 + BLOB_PHASE[i])
        r = BLOB_RADIUS[i] * scale
        shapes.append((x, y, 2 * r, 2 * r, r))
    return shapes


_LOOK_FUNCTIONS: dict[str, Callable[[str, float, float], list[Shape]]] = {
    "dot": _dot,
    "eyes": _eyes,
    "equalizer": _equalizer,
    "blobs": _blobs,
}


def look_shapes(look: str, state: str, t: float, pulse: float = 0.0) -> list[Shape]:
    """The shapes of `look` for `state` at time `t` (seconds); pulse is 0..1."""
    function = _LOOK_FUNCTIONS.get(look)
    if function is None:
        raise ValueError(f"unknown look: {look!r}")
    return function(state, t, pulse)
