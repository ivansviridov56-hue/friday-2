"""Turns raw cover bytes into a data URL the page can show."""

from __future__ import annotations

import base64


def to_data_url(data: bytes | None) -> str | None:
    """PNG or JPEG bytes -> data URL; None for empty or unknown data."""
    if not data:
        return None
    if data.startswith(b"\x89PNG"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8"):
        mime = "image/jpeg"
    else:
        return None
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
