"""Pure logic for the accent colour of the win11 theme (no registry calls here)."""

from __future__ import annotations

from collections.abc import Sequence

from friday.backdrop_logic import hex_to_rgb

# Windows keeps 8 shades in AccentPalette, from the lightest to the darkest.
# In dark mode the Settings app uses index 1 as the accent and index 0 as the light one.
ACCENT_INDEX = 1
LIGHT_INDEX = 0


def parse_palette(data: bytes) -> list[str]:
    """Registry AccentPalette (4 bytes per colour: R, G, B, unused) -> ['#rrggbb', ...]."""
    if len(data) < 8 or len(data) % 4 != 0:
        raise ValueError(f"unexpected palette size: {len(data)}")
    return [
        f"#{data[i]:02x}{data[i + 1]:02x}{data[i + 2]:02x}"
        for i in range(0, len(data), 4)
    ]


def pick_accent(palette: Sequence[str]) -> tuple[str, str]:
    """Return (accent, light) from the palette."""
    if len(palette) <= max(ACCENT_INDEX, LIGHT_INDEX):
        raise ValueError("palette is too short")
    return palette[ACCENT_INDEX], palette[LIGHT_INDEX]


def shade(color: str, factor: float) -> str:
    """Darken '#rrggbb': factor 1 keeps it, 0 gives black."""
    factor = min(max(factor, 0.0), 1.0)
    red, green, blue = (round(c * factor) for c in hex_to_rgb(color))
    return f"#{red:02x}{green:02x}{blue:02x}"


def rgb_triplet(color: str) -> str:
    """'#4cc2ff' -> '76, 194, 255' (for rgba(var(--accent-rgb), 0.4) in CSS)."""
    return ", ".join(str(c) for c in hex_to_rgb(color))


def accent_vars(accent: str, light: str) -> dict[str, str]:
    """CSS variables the page sets for the win11 theme."""
    return {
        "--accent": accent,
        "--accent-light": light,
        "--accent-rgb": rgb_triplet(accent),
        "--idle-1": shade(accent, 0.8),
        "--idle-2": shade(accent, 0.55),
        "--idle-3": shade(accent, 0.3),
    }
