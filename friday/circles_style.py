"""Which look the background circles have. The page draws it (friday/ui/circles/)."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

CIRCLE_STYLES = ("classic", "blobs", "equalizer", "dots")
DEFAULT_STYLE = "classic"


def parse_circles_style(value: str | None) -> str:
    """Value of CIRCLES from .env -> a known style name; anything else gives the default."""
    name = (value or "").strip().lower()
    if not name:
        return DEFAULT_STYLE
    if name in CIRCLE_STYLES:
        return name
    log.warning(
        "unknown CIRCLES value %r, using %s (known: %s)",
        name,
        DEFAULT_STYLE,
        ", ".join(CIRCLE_STYLES),
    )
    return DEFAULT_STYLE
