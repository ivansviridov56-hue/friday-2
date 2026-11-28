"""Tray icon (pystray). Glue only; checked live, no unit tests."""

from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger(__name__)

TITLE = "Пятница"


def _make_image():
    from friday.tray_icon import make_tray_icon

    return make_tray_icon()


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
