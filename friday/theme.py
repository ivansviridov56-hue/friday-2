"""Colour theme of the window. The page applies it (friday/ui/themes/)."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

THEMES = ("classic", "windows", "black")
DEFAULT_THEME = "classic"


def parse_theme(value: str | None) -> str:
    """Value of THEME from .env -> a known theme name; anything else gives the default."""
    name = (value or "").strip().lower()
    if not name:
        return DEFAULT_THEME
    if name in THEMES:
        return name
    log.warning(
        "unknown THEME value %r, using %s (known: %s)",
        name,
        DEFAULT_THEME,
        ", ".join(THEMES),
    )
    return DEFAULT_THEME
