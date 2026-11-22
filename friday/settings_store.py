"""Saved choices of the settings screen: data/settings.json (git-ignored)."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path

from friday.circles_style import CIRCLE_STYLES
from friday.theme import THEMES

log = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"

# Every saved key and the values it may have. Anything else is dropped.
CHOICES: dict[str, tuple[str, ...]] = {"theme": THEMES, "circles": CIRCLE_STYLES}


def _clean(raw: object) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        key: value
        for key, value in raw.items()
        if key in CHOICES and isinstance(value, str) and value in CHOICES[key]
    }


class SettingsStore:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self._path = path

    def load(self) -> dict[str, str]:
        """Saved choices; a missing, broken or odd file gives an empty dict."""
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            log.warning("could not read %s, ignoring it", self._path.name)
            return {}
        return _clean(raw)

    def save(self, values: Mapping[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(_clean(values), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp, self._path)
