"""Pure logic for the Windows 11 theme backdrop (no Windows calls here)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Acrylic through SetWindowCompositionAttribute appeared in Windows 10 1803.
MIN_BUILD = 17134
DEFAULT_TINT = "#202020"
DEFAULT_OPACITY = 0.6
KICK_DELAY = 0.6


@dataclass(frozen=True)
class Step:
    """One application of the backdrop: with or without extending the glass."""

    extend: bool
    delay: float  # seconds to wait before this step


# Applying the same value twice does nothing, so the frame is changed and
# changed back. Found live: without this the blur shows up only after a
# wallpaper change.
KICK_STEPS: tuple[Step, ...] = (
    Step(True, 0.0),
    Step(False, KICK_DELAY),
    Step(True, 0.0),
)


# Changing only the tint: one step. If the blur goes flat after a change while the window
# is inactive, use KICK_STEPS here instead (the window blinks, like at start).
CHANGE_STEPS: tuple[Step, ...] = (Step(True, 0.0),)

# Tint colour of the Windows acrylic per theme: the colour the window had when it was opaque.
# No colour may be pure black: with opacity 0 the whole GradientColor would be 0, and Windows
# then ignores the tint and draws its own black (found live: the black theme never changed).
TINT_COLORS: dict[str, str] = {
    "classic": "#0c0f1d",
    "windows": "#202020",
    "black": "#0E0E0E",
    "win11": "#202020",
}


def tint_for(theme: str) -> str:
    return TINT_COLORS.get(theme, DEFAULT_TINT)


def opacity_for(percent: int) -> float:
    """Opacity of the Windows tint (0..1): 0 % transparency is opaque, 100 % has no tint."""
    clamped = min(max(percent, 0), 100)
    return round((100 - clamped) / 100, 2)


def parse_accent(raw: int) -> str:
    """Convert the registry AccentColor DWORD (0xAABBGGRR) to '#rrggbb'."""
    if not 0 <= raw <= 0xFFFFFFFF:
        raise ValueError(f"accent out of range: {raw}")
    red = raw & 0xFF
    green = (raw >> 8) & 0xFF
    blue = (raw >> 16) & 0xFF
    return f"#{red:02x}{green:02x}{blue:02x}"


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Parse '#rrggbb' into (r, g, b)."""
    text = color.strip()
    if len(text) != 7 or text[0] != "#":
        raise ValueError(f"expected '#rrggbb', got {color!r}")
    return int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16)


def make_tint(color: str = DEFAULT_TINT, opacity: float = DEFAULT_OPACITY) -> int:
    """Build the GradientColor value 0xAABBGGRR from '#rrggbb' and opacity 0..1."""
    red, green, blue = hex_to_rgb(color)
    alpha = round(min(max(opacity, 0.0), 1.0) * 255)
    return (alpha << 24) | (blue << 16) | (green << 8) | red


def backdrop_supported(build: int) -> bool:
    """True when this Windows build can show the blur."""
    return build >= MIN_BUILD


def run_steps(
    apply: Callable[[bool], bool],
    steps: Sequence[Step] = KICK_STEPS,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Run the steps in order; stop and return False on the first failure."""
    for step in steps:
        if step.delay > 0:
            sleep(step.delay)
        try:
            ok = apply(step.extend)
        except Exception:
            log.exception("backdrop step raised")
            return False
        if not ok:
            log.warning("backdrop step failed")
            return False
    return True


def enable_backdrop(
    apply: Callable[[bool], bool],
    build: int,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Turn the blur on; False means the theme must fall back to plain grey."""
    if not backdrop_supported(build):
        log.info("backdrop not supported on build %s", build)
        return False
    return run_steps(apply, KICK_STEPS, sleep)
