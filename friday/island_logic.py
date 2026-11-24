"""Pure logic of the top-edge island: size, position and colours."""

from __future__ import annotations
import math
from typing import NamedTuple

ISLAND_WIDTH = 120
ISLAND_HEIGHT = 32
TOP_MARGIN = 8

DEFAULT_COLOR = "#4c8dff"
DEFAULT_THEME = "classic"

STATE_COLORS: dict[str, str] = {
    "loading": "#4c8dff",
    "idle": "#4c8dff",
    "listening": "#ff5c8a",
    "thinking": "#9b6bff",
    "speaking": "#2fd4e6",
    "error": "#ff4d4d",
}

_GREY_STATES: dict[str, str] = {
    "loading": "#8c8c8c",
    "idle": "#8c8c8c",
    "listening": "#e5719b",
    "thinking": "#a995e8",
    "speaking": "#62cdb4",
    "error": "#ee6a45",
}

# classic keeps the original colours; black and win11 are temporary copies of windows
_BLACK_STATES: dict[str, str] = {
    "loading": "#e6e6e6",
    "idle": "#e6e6e6",
    "listening": "#ff5c9a",
    "thinking": "#a283ff",
    "speaking": "#3de0b4",
    "error": "#ff5a32",
}

_WIN11_STATES: dict[str, str] = {
    **_GREY_STATES,
    "loading": "#3aa6d8",
    "idle": "#3aa6d8",
}

STATE_COLORS_BY_THEME: dict[str, dict[str, str]] = {
    "classic": STATE_COLORS,
    "windows": _GREY_STATES,
    "black": _BLACK_STATES,
    "win11": _WIN11_STATES,
}
BODY_COLORS: dict[str, str] = {
    "classic": "#0c0f1d",
    "windows": "#202020",
    "black": "#010101",
    "win11": "#202020",
}
TEXT_COLORS: dict[str, str] = {
    "classic": "#d1d9ff",
    "windows": "#f2f2f2",
    "black": "#ececec",
    "win11": "#ffffff",
}


def island_position(
    screen_width: int,
    width: int = ISLAND_WIDTH,
    top_margin: int = TOP_MARGIN,
) -> tuple[int, int]:
    """Return (x, y) of the island: centred horizontally, near the top edge."""
    if screen_width <= 0 or width <= 0 or top_margin < 0:
        raise ValueError("screen width, island width and margin must be positive")
    return max(0, (screen_width - width) // 2), top_margin


def color_for(state: str, theme: str = DEFAULT_THEME) -> str:
    """Colour of a state in a theme; unknown theme or state falls back to the defaults."""
    colors = STATE_COLORS_BY_THEME.get(theme, STATE_COLORS)
    return colors.get(state, DEFAULT_COLOR)


def body_for(theme: str) -> str:
    return BODY_COLORS.get(theme, BODY_COLORS[DEFAULT_THEME])


def text_color_for(theme: str) -> str:
    return TEXT_COLORS.get(theme, TEXT_COLORS[DEFAULT_THEME])


MAX_TEXT_CHARS = 160


def clip_text(text: str, limit: int = MAX_TEXT_CHARS) -> str:
    """Collapse whitespace; if the text is too long keep its END, like subtitles.

    The cut falls on a word start; a leading "…" marks the cut (so the result may be
    one character longer than the limit).
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    tail = clean[-limit:]
    if clean[-limit - 1] != " ":
        cut = tail.find(" ")
        if cut != -1:
            tail = tail[cut + 1 :]
    return "…" + tail


class WaveParams(NamedTuple):
    amplitude: float  # px, how far the bottom edge moves
    speed: float  # radians per second
    spatial: float  # how many waves fit across the island


MAX_WAVE_AMPLITUDE = 3.0
LINE_GAP = 3.0  # px between the island edge and the light line under it
WAVE_PAD = 8  # transparent px under the island, room for the wave and the line

WAVE_BY_STATE: dict[str, WaveParams] = {
    "loading": WaveParams(1.5, 2.4, 1.2),
    "idle": WaveParams(1.5, 1.2, 1.0),
    "listening": WaveParams(3.0, 3.0, 1.5),
    "thinking": WaveParams(2.0, 5.0, 3.0),
    "speaking": WaveParams(2.4, 2.4, 1.6),
    "error": WaveParams(0.8, 0.8, 1.0),
}


def wave_params(state: str) -> WaveParams:
    """Wave settings of a state; an unknown state moves like idle."""
    return WAVE_BY_STATE.get(state, WAVE_BY_STATE["idle"])


def wave_offset(
    x: float, width: float, phase: float, amplitude: float, spatial: float
) -> float:
    """Vertical shift (px, positive = down) of the bottom edge at x in 0..width.

    Two sines with different wavelengths; the shift fades to zero at both ends,
    so the wave joins the rounded corners smoothly.
    """
    if width <= 0:
        raise ValueError("width must be positive")
    u = min(max(x / width, 0.0), 1.0)
    taper = math.sin(math.pi * u)
    main = math.sin(2 * math.pi * spatial * u + phase)
    side = math.sin(2 * math.pi * spatial * 1.7 * u - phase * 0.7 + 1.3)
    return amplitude * taper * (0.65 * main + 0.35 * side)


def edge_gap(x: float, width: float) -> float:
    """Distance of the light line from the edge: zero at the ends, LINE_GAP in the middle."""
    if width <= 0:
        raise ValueError("width must be positive")
    u = min(max(x / width, 0.0), 1.0)
    return LINE_GAP * math.sin(math.pi * u)


def ease_params(current: WaveParams, target: WaveParams, k: float) -> WaveParams:
    """Move the wave settings a fraction k (0..1) of the way to the target."""
    if not 0.0 <= k <= 1.0:
        raise ValueError("k must be between 0 and 1")
    return WaveParams(*(c + (t - c) * k for c, t in zip(current, target)))
