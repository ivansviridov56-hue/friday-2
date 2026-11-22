"""The user's choices (theme, circles look): saved file first, .env second."""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping
from typing import Callable, Protocol

from friday.circles_style import CIRCLE_STYLES, parse_circles_style
from friday.settings_store import CHOICES
from friday.theme import THEMES, parse_theme
from friday.ui_events import CirclesStyleChanged, ThemeChanged, UiEvent, UiEventBus

log = logging.getLogger(__name__)


class Store(Protocol):
    def load(self) -> dict[str, str]: ...

    def save(self, values: Mapping[str, str]) -> None: ...


class SettingsService:
    def __init__(
        self, bus: UiEventBus, store: Store, env: Mapping[str, str | None]
    ) -> None:
        self._bus = bus
        self._store = store
        self._lock = threading.Lock()
        saved = store.load()
        self._values: dict[str, str] = {
            "theme": saved.get("theme") or parse_theme(env.get("THEME")),
            "circles": saved.get("circles") or parse_circles_style(env.get("CIRCLES")),
        }

    def publish_initial(self) -> None:
        """Send the starting choices to the window (the bus remembers them)."""
        with self._lock:
            values = dict(self._values)
        self._bus.publish(CirclesStyleChanged(values["circles"]))
        self._bus.publish(ThemeChanged(values["theme"]))

    def set_theme(self, name: str) -> bool:
        return self._set("theme", name, ThemeChanged)

    def set_circles(self, name: str) -> bool:
        return self._set("circles", name, CirclesStyleChanged)

    def snapshot(self) -> dict:
        """Current choices and the lists of allowed values, for the settings panel."""
        with self._lock:
            current = dict(self._values)
        return {
            "current": current,
            "themes": list(THEMES),
            "circles": list(CIRCLE_STYLES),
        }

    def _set(self, key: str, name: str, make_event: Callable[[str], UiEvent]) -> bool:
        if name not in CHOICES[key]:
            return False
        with self._lock:
            self._values[key] = name
            values = dict(self._values)
        self._bus.publish(make_event(name))
        try:
            self._store.save(values)
        except OSError:
            log.exception("could not save settings")
        return True
