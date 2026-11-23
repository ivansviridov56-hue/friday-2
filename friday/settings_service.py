"""The user's choices (theme, circles look): saved file first, .env second."""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping
from typing import Any, Callable, Protocol

from friday.circles_style import CIRCLE_STYLES, parse_circles_style
from friday.settings_store import CHOICES
from friday.theme import THEMES, parse_theme
from friday.ui_events import (
    CirclesStyleChanged,
    ThemeChanged,
    UiEvent,
    UiEventBus,
    TransparencyChanged,
)
from friday.transparency import clean_percents, parse_percent, percent_for

log = logging.getLogger(__name__)


class Store(Protocol):
    def load(self) -> dict[str, Any]: ...

    def save(self, values: Mapping[str, Any]) -> None: ...


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
        self._percents: dict[str, int] = clean_percents(saved.get("transparency"))

    def publish_initial(self) -> None:
        """Send the starting choices to the window (the bus remembers them)."""
        with self._lock:
            values = dict(self._values)
            percent = percent_for(values["theme"], self._percents)
        self._bus.publish(CirclesStyleChanged(values["circles"]))
        self._bus.publish(ThemeChanged(values["theme"]))
        self._bus.publish(TransparencyChanged(percent))

    def set_theme(self, name: str) -> bool:
        if not self._set("theme", name, ThemeChanged):
            return False
        with self._lock:
            percent = percent_for(self._values["theme"], self._percents)
        self._bus.publish(TransparencyChanged(percent))
        return True

    def set_transparency(self, percent: object) -> bool:
        """Set the transparency of the CURRENT theme; each theme keeps its own."""
        value = parse_percent(percent)
        if value is None:
            return False
        with self._lock:
            self._percents[self._values["theme"]] = value
            values = self._to_save()
        self._bus.publish(TransparencyChanged(value))
        self._save(values)
        return True

    def set_circles(self, name: str) -> bool:
        return self._set("circles", name, CirclesStyleChanged)

    def snapshot(self) -> dict:
        """Current choices and the lists of allowed values, for the settings panel."""
        with self._lock:
            current = dict(self._values)
            percents = {t: percent_for(t, self._percents) for t in THEMES}
        return {
            "current": current,
            "themes": list(THEMES),
            "circles": list(CIRCLE_STYLES),
            "percents": percents,
        }

    def _to_save(self) -> dict[str, Any]:
        """What goes to the file; the caller holds the lock."""
        return {**self._values, "transparency": dict(self._percents)}

    def _save(self, values: Mapping[str, Any]) -> None:
        try:
            self._store.save(values)
        except OSError:
            log.exception("could not save settings")

    def _set(self, key: str, name: str, make_event: Callable[[str], UiEvent]) -> bool:
        if name not in CHOICES[key]:
            return False
        with self._lock:
            self._values[key] = name
            values = self._to_save()
        self._bus.publish(make_event(name))
        self._save(values)
        return True
