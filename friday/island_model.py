"""Animation model of the island: the window only draws what this model says. No Qt here.

Text is measured by a callable given from outside (Qt in the app, a fake in the tests):
measure(text) -> (width, height) of the text wrapped at WRAP_W.
"""

from __future__ import annotations

import math
from typing import Callable

from friday.island_logic import (
    DEFAULT_THEME,
    WAVE_EASE_RATE,
    blend_factor,
    body_for,
    color_for,
    ease_params,
    ease_width,
    scroll_for,
    smoothstep,
    step_toward,
    target_body_width,
    text_color_for,
    visible_lines_height,
    wave_params,
)
from friday.island_looks import DEFAULT_LOOK, Shape, look_or_default, look_shapes
from friday.text_reveal import progress_at, reveal_end
from friday.word_fade import Span, add_span, build_markup, live_spans

Measure = Callable[[str], tuple[float, float]]

CAP_W = 150  # body width when collapsed
CAP_H = 34  # body height when collapsed
EXP_W = 440  # the widest the body gets
PAD_V = 9
TEXT_LEFT = 40
TEXT_RIGHT = 18
MAX_LINES = 2
WRAP_W = EXP_W - TEXT_LEFT - TEXT_RIGHT  # text is always wrapped at this width
EXPAND_SECONDS = 0.45
WIDTH_EASE_RATE = 14.0
SCROLL_EASE_RATE = 10.0
COLOR_SECONDS = 0.35
PULSE_SECONDS = 1.3
PULSING = frozenset({"listening", "speaking"})
MAX_TICK = 0.1  # a longer pause between ticks counts as this long


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _rgb(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix_hex(a: str, b: str, t: float) -> str:
    """Colour between a and b ('#rrggbb'); t is clamped to 0..1."""
    t = min(max(t, 0.0), 1.0)
    mixed = (round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


class IslandModel:
    def __init__(self, measure: Measure, line_height: float) -> None:
        if line_height <= 0:
            raise ValueError("line_height must be positive")
        self._measure = measure
        self._line_h = float(line_height)
        self._state = "idle"
        self._theme = DEFAULT_THEME
        self._accent: str | None = None
        start = color_for("idle", DEFAULT_THEME)
        self._color_from = start
        self._color_to = start
        self._color_t = 1.0
        self._body = body_for(DEFAULT_THEME)
        self._text_color = text_color_for(DEFAULT_THEME)
        self._wave = wave_params("idle")
        self._phase = 0.0
        self._pulse_t = 0.0
        self._text = ""
        self._reveal = False
        self._shown = 0
        self._base = 0
        self._active: tuple[int, int, float, float] | None = None
        self._expand_p = 0.0
        self._expand_target = 0.0
        self._expand = 0.0
        self._open_w = float(CAP_W)
        self._target_w = float(CAP_W)
        self._open_lines_h = self._line_h
        self._target_lines_h = self._line_h
        self._scroll = 0.0
        self._target_scroll = 0.0
        self._width_key = -1
        self._spans: list[Span] = []
        self._now = 0.0
        self._look = DEFAULT_LOOK
        self._icon_t = 0.0

    # ---- what the window draws ----
    @property
    def expand(self) -> float:
        return self._expand

    @property
    def body_w(self) -> float:
        return _lerp(CAP_W, self._open_w, self._expand)

    @property
    def body_h(self) -> float:
        open_h = max(CAP_H, self._open_lines_h + 2 * PAD_V)
        return _lerp(CAP_H, open_h, self._expand)

    @property
    def lines_h(self) -> float:
        return self._open_lines_h

    @property
    def scroll(self) -> float:
        return self._scroll

    @property
    def phase(self) -> float:
        return self._phase

    @property
    def wave_amplitude(self) -> float:
        return self._wave.amplitude

    @property
    def wave_spatial(self) -> float:
        return self._wave.spatial

    @property
    def pulse(self) -> float:
        if self._state not in PULSING:
            return 0.0
        return 0.5 - 0.5 * math.cos(2 * math.pi * self._pulse_t / PULSE_SECONDS)

    @property
    def dot_color(self) -> str:
        return mix_hex(self._color_from, self._color_to, smoothstep(self._color_t))

    @property
    def body_color(self) -> str:
        return self._body

    @property
    def text_color(self) -> str:
        return self._text_color

    @property
    def visible_text(self) -> str:
        return self._text[: self._shown] if self._reveal else self._text

    @property
    def text_alpha(self) -> float:
        if not self._text:
            return 0.0
        return min(1.0, max(0.0, (self._expand - 0.5) * 2))

    @property
    def markup(self) -> str:
        return build_markup(self.visible_text, self._spans, self._now, self._fade_color)

    def _fade_color(self, alpha: float) -> str:
        return mix_hex(self._body, self._text_color, alpha)

    @property
    def look(self) -> str:
        return self._look

    @property
    def icon_shapes(self) -> list[Shape]:
        return look_shapes(self._look, self._state, self._icon_t, self.pulse)

    # ---- commands ----
    def set_state(self, state: str) -> None:
        was_pulsing = self._state in PULSING
        self._color_from = self.dot_color
        self._color_to = color_for(state, self._theme, self._accent)
        self._color_t = 0.0
        self._state = state
        if state in PULSING and not was_pulsing:
            self._pulse_t = 0.0

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._body = body_for(theme)
        self._text_color = text_color_for(theme)
        self.set_state(self._state)

    def set_accent(self, accent: str) -> None:
        """Windows accent colour; only the win11 theme uses it (see color_for)."""
        self._accent = accent
        self.set_state(self._state)

    def set_look(self, name: str) -> None:
        self._look = look_or_default(name)

    def show_text(self, text: str) -> None:
        self._spans = []
        self._reveal = False
        self._text = text
        self._width_key = -1
        self._update_targets()
        self._open_w = self._target_w
        self._open_lines_h = self._target_lines_h
        self._scroll = self._target_scroll
        self._expand_target = 1.0

    def clear_text(self) -> None:
        self._expand_target = 0.0

    def start_reveal(self, text: str) -> None:
        self._spans = []
        self._text = text
        self._reveal = True
        self._shown = 0
        self._base = 0
        self._active = None
        self._width_key = -1
        self._open_w = float(CAP_W)
        self._target_w = float(CAP_W)
        self._open_lines_h = self._line_h
        self._target_lines_h = self._line_h
        self._scroll = 0.0
        self._target_scroll = 0.0
        self._expand_target = 1.0

    def reveal_chunk(self, start: int, end: int, seconds: float, now: float) -> None:
        self._now = now
        if not self._reveal:
            return
        if self._active is not None:
            self._base = max(self._base, self._active[1])
        self._base = max(self._base, min(start, len(self._text)))
        self._active = (start, end, seconds, now)
        self._update_reveal(now)

    def finish_reveal(self) -> None:
        if not self._reveal:
            return
        self._reveal = False
        self._active = None
        self._spans = add_span(self._spans, self._shown, len(self._text), self._now)
        self._shown = len(self._text)

    def tick(self, dt: float, now: float) -> None:
        dt = min(max(dt, 0.0), MAX_TICK)
        self._now = now
        self._wave = ease_params(
            self._wave, wave_params(self._state), blend_factor(dt, WAVE_EASE_RATE)
        )
        self._phase += dt * self._wave.speed
        self._pulse_t += dt
        self._icon_t += dt
        self._color_t = min(1.0, self._color_t + dt / COLOR_SECONDS)
        self._step_expand(dt)
        self._update_reveal(now)
        self._spans = live_spans(self._spans, now)
        self._update_targets()
        self._open_w = ease_width(self._open_w, self._target_w, dt, WIDTH_EASE_RATE)
        self._open_lines_h = ease_width(
            self._open_lines_h, self._target_lines_h, dt, WIDTH_EASE_RATE
        )
        self._scroll = ease_width(
            self._scroll, self._target_scroll, dt, SCROLL_EASE_RATE
        )

    # ---- inside ----
    def _step_expand(self, dt: float) -> None:
        if self._expand_p == self._expand_target:
            return
        self._expand_p = step_toward(
            self._expand_p, self._expand_target, dt, EXPAND_SECONDS
        )
        self._expand = smoothstep(self._expand_p)
        if self._expand_p == self._expand_target and self._expand <= 0.0:
            self._forget_text()

    def _forget_text(self) -> None:
        self._spans = []
        self._text = ""
        self._reveal = False
        self._active = None
        self._shown = 0
        self._open_w = float(CAP_W)
        self._target_w = float(CAP_W)
        self._open_lines_h = self._line_h
        self._target_lines_h = self._line_h
        self._scroll = 0.0
        self._target_scroll = 0.0
        self._width_key = -1

    def _update_reveal(self, now: float) -> None:
        if not self._reveal:
            return
        shown = self._base
        if self._active is not None:
            start, end, seconds, t0 = self._active
            progress = progress_at(now - t0, seconds)
            shown = max(shown, reveal_end(self._text, start, end, progress))
        if shown > self._shown:
            self._spans = add_span(self._spans, self._shown, shown, now)
        self._shown = shown

    def _update_targets(self) -> None:
        text = self.visible_text
        if len(text) == self._width_key:
            return
        self._width_key = len(text)
        width, height = self._measure(text) if text else (0.0, 0.0)
        self._target_w = target_body_width(width, CAP_W, EXP_W, TEXT_LEFT, TEXT_RIGHT)
        self._target_lines_h = max(
            self._line_h, visible_lines_height(height, self._line_h, MAX_LINES)
        )
        self._target_scroll = scroll_for(height, self._line_h, MAX_LINES)
