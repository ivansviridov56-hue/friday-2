"""Window transparency per theme, in percent (0 = opaque, 100 = fully see-through)."""

from __future__ import annotations

import math
from collections.abc import Mapping

from friday.theme import THEMES

MIN_PERCENT = 0
MAX_PERCENT = 100

# win11 keeps the look it had with the fixed 60 % tint (60 % tint = 40 % transparency).
DEFAULT_PERCENT: dict[str, int] = {
    "classic": 0,
    "windows": 0,
    "black": 0,
    "win11": 40,
}


def parse_percent(value: object) -> int | None:
    """A whole percent 0..100, or None if the value is not a usable number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    percent = round(value)
    if not MIN_PERCENT <= percent <= MAX_PERCENT:
        return None
    return percent


def default_percent(theme: str) -> int:
    return DEFAULT_PERCENT.get(theme, 0)


def clean_percents(raw: object) -> dict[str, int]:
    """Keep only known themes with valid percents; anything else is dropped."""
    if not isinstance(raw, Mapping):
        return {}
    cleaned: dict[str, int] = {}
    for theme, value in raw.items():
        if theme not in THEMES:
            continue
        percent = parse_percent(value)
        if percent is not None:
            cleaned[theme] = percent
    return cleaned


def percent_for(theme: str, saved: Mapping[str, int]) -> int:
    """Saved percent of the theme, or its default."""
    percent = parse_percent(saved.get(theme))
    return percent if percent is not None else default_percent(theme)
