"""UI-facing events: assistant state and chat messages.

Independent of any window toolkit, so it can be tested without a GUI.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Literal

logger = logging.getLogger(__name__)


class State(str, Enum):
    LOADING = "loading"
    ERROR = "error"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


@dataclass(frozen=True)
class StateChanged:
    state: State


@dataclass(frozen=True)
class MessageAdded:
    """`spoken=False`: the answer is only shown, it will not be voiced."""

    role: Literal["user", "assistant"]
    text: str
    spoken: bool = True


@dataclass(frozen=True)
class SpeechChunkStarted:
    """One piece of her answer starts to sound: its text (as cleaned for speech) and its
    length in seconds. Not remembered by the bus."""

    text: str
    seconds: float


@dataclass(frozen=True)
class LevelChanged:
    """Microphone loudness 0..1 for the window; not remembered by the bus."""

    level: float


@dataclass(frozen=True)
class CoverChanged:
    """Cover of the current track as a data URL; None hides the music circle."""

    image: str | None


@dataclass(frozen=True)
class CirclesStyleChanged:
    """Look of the background circles (see friday/circles_style.py); remembered by the bus."""

    name: str


@dataclass(frozen=True)
class ThemeChanged:
    """Colour theme of the window (see friday/theme.py); remembered by the bus."""

    name: str


@dataclass(frozen=True)
class AccentChanged:
    """Accent colours of Windows (see friday/accent_logic.py); remembered by the bus."""

    accent: str
    light: str


@dataclass(frozen=True)
class WallpaperChanging:
    """The wallpaper is about to change; the page covers the blur snap. Not remembered by the bus."""


@dataclass(frozen=True)
class TransparencyChanged:
    """Window transparency of the current theme, percent 0..100; remembered by the bus."""

    percent: int


@dataclass(frozen=True)
class IslandLookChanged:
    """Look of the island icon (see friday/island_looks.py); remembered by the bus."""

    name: str


UiEvent = (
    StateChanged
    | MessageAdded
    | SpeechChunkStarted
    | LevelChanged
    | CoverChanged
    | CirclesStyleChanged
    | ThemeChanged
    | AccentChanged
    | TransparencyChanged
    | IslandLookChanged
    | WallpaperChanging
)
Listener = Callable[[UiEvent], None]


class UiEventBus:
    """Thread-safe publish/subscribe. A failing listener never breaks others.

    Remembers the last state: a listener that subscribes late gets it at once,
    so it never misses a state published before it joined.
    """

    def __init__(self) -> None:
        self._listeners: list[Listener] = []
        self._last_state: StateChanged | None = None
        self._last_cover: CoverChanged | None = None
        self._last_style: CirclesStyleChanged | None = None
        self._last_theme: ThemeChanged | None = None
        self._last_accent: AccentChanged | None = None
        self._last_transparency: TransparencyChanged | None = None
        self._last_island_look: IslandLookChanged | None = None
        self._lock = threading.Lock()

    def subscribe(self, listener: Listener) -> None:
        with self._lock:
            self._listeners.append(listener)
            replay = [
                e
                for e in (
                    self._last_theme,
                    self._last_transparency,
                    self._last_island_look,
                    self._last_accent,
                    self._last_state,
                    self._last_cover,
                    self._last_style,
                )
                if e is not None
            ]
        for event in replay:
            self._deliver(listener, event)

    def unsubscribe(self, listener: Listener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def publish(self, event: UiEvent) -> None:
        with self._lock:
            if isinstance(event, StateChanged):
                self._last_state = event
            elif isinstance(event, CoverChanged):
                self._last_cover = event
            elif isinstance(event, CirclesStyleChanged):
                self._last_style = event
            elif isinstance(event, ThemeChanged):
                self._last_theme = event
            elif isinstance(event, TransparencyChanged):
                self._last_transparency = event
            elif isinstance(event, AccentChanged):
                self._last_accent = event
            elif isinstance(event, IslandLookChanged):
                self._last_island_look = event
            listeners = list(self._listeners)
        for listener in listeners:
            self._deliver(listener, event)

    @staticmethod
    def _deliver(listener: Listener, event: UiEvent) -> None:
        try:
            listener(event)
        except Exception:
            logger.exception("UI listener failed on %r", event)
