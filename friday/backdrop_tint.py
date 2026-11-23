"""Turns theme and transparency events into the colour and opacity of the Windows tint."""

from __future__ import annotations

from collections.abc import Callable

from friday.backdrop_logic import opacity_for, tint_for
from friday.ui_events import ThemeChanged, TransparencyChanged, UiEvent


class BackdropTint:
    """Calls on_tint(colour, opacity) only when the wanted tint really changes.

    The settings service always sends the transparency right after a theme, so the
    tint is computed on the transparency event, with the latest theme.
    """

    def __init__(self, on_tint: Callable[[str, float], None]) -> None:
        self._on_tint = on_tint
        self._theme: str | None = None
        self._last: tuple[str, float] | None = None

    def on_event(self, event: UiEvent) -> None:
        if isinstance(event, ThemeChanged):
            self._theme = event.name
        elif isinstance(event, TransparencyChanged):
            if self._theme is None:
                return
            tint = (tint_for(self._theme), opacity_for(event.percent))
            if tint != self._last:
                self._last = tint
                self._on_tint(*tint)
