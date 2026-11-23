"""Tray icon (pystray). Glue only; checked live, no unit tests."""

from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger(__name__)

TITLE = "Пятница"


def _make_image():
    from PIL import Image, ImageDraw

    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, size - 4, size - 4), fill=(47, 94, 241, 255))
    draw.ellipse((20, 20, size - 20, size - 20), fill=(209, 217, 255, 255))
    return image


class Tray:
    """Tray icon with the menu "Открыть" (also the default click) and "Выйти"."""

    def __init__(
        self, on_open: Callable[[], object], on_quit: Callable[[], object]
    ) -> None:
        self._on_open = on_open
        self._on_quit = on_quit
        self._icon = None

    def start(self) -> None:
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem(
                "Открыть", lambda icon, item: self._on_open(), default=True
            ),
            pystray.MenuItem("Выйти", lambda icon, item: self._on_quit()),
        )
        self._icon = pystray.Icon("friday", _make_image(), TITLE, menu)
        self._icon.run_detached()

    def close(self) -> None:
        if self._icon is None:
            return
        try:
            self._icon.stop()
        except Exception:
            log.exception("could not stop the tray icon")
        self._icon = None
