"""The Qt island window. Runs as its own process: python -m friday.island_qt

Commands arrive on stdin, one per line: "state <name>", "theme <name>",
"text <base64>", "clear" or "quit". The process prints "ready" once the window is
shown and exits when stdin closes (the parent is gone). Text is never logged.
"""

from __future__ import annotations

import base64
import binascii
import sys
import os
import time
import threading

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPointF,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget

from friday.island_logic import (
    DEFAULT_THEME,
    WAVE_PAD,
    body_for,
    color_for,
    ease_params,
    edge_gap,
    text_color_for,
    wave_offset,
    wave_params,
    WAVE_EASE_RATE,
    blend_factor,
    smoothstep,
    step_toward,
    ease_width,
    target_body_width,
    visible_lines_height,
    scroll_for,
)
from friday.text_reveal import progress_at, reveal_end

CAP_W = 150  # width of the straight part when collapsed
CAP_H = 34  # height when collapsed; the island hangs from the top edge of the screen
EXP_W = 440  # width of the straight part when the text is shown
FLARE = 10  # the concave curve that joins the island to the screen edge
RADIUS = 14  # rounding of the bottom corners
DOT_LEFT = 22  # dot position (from the body's left edge) when expanded
TEXT_LEFT = 40
TEXT_RIGHT = 18
PAD_V = 9
MAX_LINES = 2
FONT_PX = 13
MAX_PAYLOAD = 8000  # base64 characters accepted per text command
PULSING = {"listening", "speaking"}
WAVE_STEP = 3  # px between the points of the wavy edge
WAVE_LAG = 0.5  # the light line follows the edge a little later (radians)
WAVE_TICK_MS = 6  # about 165 frames per second
EXPAND_SECONDS = 0.45  # how long the island takes to open or close
WRAP_W = EXP_W - TEXT_LEFT - TEXT_RIGHT  # text is always wrapped at the widest size
WIDTH_EASE_RATE = 14.0  # how fast the island width follows the text (bigger = faster)
SCROLL_EASE_RATE = 10.0  # how fast the text scrolls up (bigger = faster)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class IslandWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._state = "idle"
        self._theme = DEFAULT_THEME
        self._color = QColor(color_for("idle"))
        self._body = QColor(body_for(DEFAULT_THEME))
        self._text_color = QColor(text_color_for(DEFAULT_THEME))
        self._pulse = 0.0
        self._wave = wave_params("idle")
        self._phase = 0.0
        self._last_tick = time.monotonic()

        self._text = ""
        self._reveal = False  # the text is revealed in step with her voice
        self._shown = 0  # how many characters are visible now
        self._base = 0  # characters already shown for good (earlier pieces)
        self._active: tuple[int, int, float, float] | None = (
            None  # start, end, seconds, t0
        )
        self._expand = 0.0
        self._expand_target = 0.0
        self._expand_p = 0.0  # linear progress 0..1; self._expand is its eased value
        self._target_h = CAP_H
        self._lines_h = 0
        self._full_h = 0
        self._open_w = float(CAP_W)  # body width when open (follows the text)
        self._target_w = float(CAP_W)
        self._width_key = -1  # length of the text the target width was measured for
        self._open_lines_h = 0.0  # height of the visible text block (eased)
        self._target_lines_h = 0.0
        self._scroll = 0.0  # how far the text is moved up now (eased)
        self._target_scroll = 0.0
        self._screen_x = 0
        self._screen_w = 0
        self._screen_y = 0

        self._font = QFont()
        self._font.setFamilies(["Rubik", "Segoe UI", "sans-serif"])
        self._font.setPixelSize(FONT_PX)
        self._max_body_h = (
            QFontMetrics(self._font).lineSpacing() * MAX_LINES + 2 * PAD_V
        )
        self._fps_on = os.environ.get("FRIDAY_ISLAND_FPS") == "1"
        self._frames = 0
        self._fps_t = time.monotonic()

        self._color_anim = QVariantAnimation(self)
        self._color_anim.setDuration(350)
        self._color_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._color_anim.valueChanged.connect(self._on_color)

        self._pulse_anim = QVariantAnimation(self)
        self._pulse_anim.setDuration(1300)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setKeyValueAt(0.0, 0.0)
        self._pulse_anim.setKeyValueAt(0.5, 1.0)
        self._pulse_anim.setKeyValueAt(1.0, 0.0)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.valueChanged.connect(self._on_pulse)

        self._wave_timer = QTimer(self)
        self._wave_timer.setInterval(WAVE_TICK_MS)
        self._wave_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._wave_timer.timeout.connect(self._on_wave_tick)
        self._wave_timer.start()
        self._place()

    def set_screen(self, x: int, y: int, width: int) -> None:
        """Remember where the top edge of the screen is, to keep the island centred."""
        self._screen_x, self._screen_y, self._screen_w = x, y, width
        self._place()

    def set_state(self, state: str) -> None:
        self._state = state
        self._color_anim.stop()
        self._color_anim.setStartValue(self._color)
        self._color_anim.setEndValue(QColor(color_for(state, self._theme)))
        self._color_anim.start()
        if state in PULSING:
            if self._pulse_anim.state() != QVariantAnimation.State.Running:
                self._pulse_anim.start()
        else:
            self._pulse_anim.stop()
            self._pulse = 0.0
            self.update()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._body = QColor(body_for(theme))
        self._text_color = QColor(text_color_for(theme))
        self.set_state(self._state)

    def show_text(self, text: str) -> None:
        self._reveal = False
        self._text = text
        self._measure()
        self._width_key = -1
        self._update_target_width()
        self._open_w = self._target_w
        self._open_lines_h = self._target_lines_h
        self._scroll = self._target_scroll
        self._animate_expand(1.0)
        self._apply_geometry()

    def clear_text(self) -> None:
        self._animate_expand(0.0)

    def start_reveal(self, text: str) -> None:
        self._text = text
        self._reveal = True
        self._shown = 0
        self._base = 0
        self._active = None
        self._measure()
        self._width_key = -1
        self._open_w = float(CAP_W)
        self._target_w = float(CAP_W)
        line_h = float(QFontMetrics(self._font).lineSpacing())
        self._open_lines_h = line_h
        self._target_lines_h = line_h
        self._scroll = 0.0
        self._target_scroll = 0.0
        self._animate_expand(1.0)
        self._apply_geometry()

    def reveal_chunk(self, start: int, end: int, seconds: float) -> None:
        if not self._reveal:
            return
        if self._active is not None:
            self._base = max(self._base, self._active[1])
        self._base = max(self._base, min(start, len(self._text)))
        self._active = (start, end, seconds, time.monotonic())
        self._update_reveal()

    def finish_reveal(self) -> None:
        if not self._reveal:
            return
        self._reveal = False
        self._active = None
        self._shown = len(self._text)
        self.update()

    def _update_reveal(self) -> None:
        if not self._reveal:
            return
        shown = self._base
        if self._active is not None:
            start, end, seconds, t0 = self._active
            progress = progress_at(time.monotonic() - t0, seconds)
            shown = max(shown, reveal_end(self._text, start, end, progress))
        self._shown = shown

    def _text_box(self, text: str) -> tuple[float, float]:
        if not text:
            return 0.0, 0.0
        flags = int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft)
        rect = QFontMetrics(self._font).boundingRect(0, 0, WRAP_W, 10000, flags, text)
        return float(rect.width()), float(rect.height())

    def _update_target_width(self) -> None:
        text = self._text[: self._shown] if self._reveal else self._text
        if len(text) == self._width_key:
            return
        self._width_key = len(text)
        width, height = self._text_box(text)
        self._target_w = target_body_width(width, CAP_W, EXP_W, TEXT_LEFT, TEXT_RIGHT)
        line_h = float(QFontMetrics(self._font).lineSpacing())
        self._target_lines_h = max(
            line_h, visible_lines_height(height, line_h, MAX_LINES)
        )
        self._target_scroll = scroll_for(height, line_h, MAX_LINES)

    def _measure(self) -> None:
        metrics = QFontMetrics(self._font)
        text_w = EXP_W - TEXT_LEFT - TEXT_RIGHT
        flags = int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft)
        full = metrics.boundingRect(0, 0, text_w, 10000, flags, self._text).height()
        self._full_h = full
        self._lines_h = min(full, metrics.lineSpacing() * MAX_LINES)
        self._target_h = max(CAP_H, self._lines_h + 2 * PAD_V)

    def _animate_expand(self, target: float) -> None:
        self._expand_target = target

    def _step_expand(self, dt: float) -> None:
        if self._expand_p == self._expand_target:
            return
        self._expand_p = step_toward(
            self._expand_p, self._expand_target, dt, EXPAND_SECONDS
        )
        self._expand = smoothstep(self._expand_p)
        self._apply_geometry()
        if self._expand_p == self._expand_target:
            self._on_expand_finished()

    def _on_expand_finished(self) -> None:
        if self._expand <= 0.0:
            self._text = ""
            self._reveal = False
            self._active = None
            self._open_w = float(CAP_W)
            self._target_w = float(CAP_W)
            self._width_key = -1
            self._scroll = 0.0
            self._target_scroll = 0.0

    def _place(self) -> None:
        """The window has a fixed size (the biggest the island can be); it never resizes."""
        width = EXP_W + 2 * FLARE
        height = max(CAP_H, self._max_body_h) + WAVE_PAD
        x = self._screen_x + (self._screen_w - width) // 2
        self.setGeometry(x, self._screen_y, width, height)

    def _apply_geometry(self) -> None:
        self.update()  # the island is drawn inside the fixed window, only a repaint is needed

    def _on_color(self, value) -> None:
        self._color = QColor(value)

    def _on_wave_tick(self) -> None:
        now = time.monotonic()
        dt = min(now - self._last_tick, 0.1)
        self._last_tick = now
        k = blend_factor(dt, WAVE_EASE_RATE)
        self._wave = ease_params(self._wave, wave_params(self._state), k)
        self._phase += dt * self._wave.speed
        self._step_expand(dt)
        self._update_reveal()
        self._update_target_width()
        self._open_w = ease_width(self._open_w, self._target_w, dt, WIDTH_EASE_RATE)
        self._open_lines_h = ease_width(
            self._open_lines_h, self._target_lines_h, dt, WIDTH_EASE_RATE
        )
        self._scroll = ease_width(
            self._scroll, self._target_scroll, dt, SCROLL_EASE_RATE
        )
        self.update()

    def _on_pulse(self, value) -> None:
        self._pulse = float(value)

    def _count_frame(self) -> None:
        self._frames += 1
        now = time.monotonic()
        if now - self._fps_t >= 1.0:
            from pathlib import Path

            log = Path(__file__).resolve().parent.parent / "data" / "island_fps.txt"
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"island fps: {self._frames}\n")
            self._frames = 0
            self._fps_t = now

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._fps_on:
            self._count_frame()
        t = self._expand
        lines_h = self._open_lines_h
        h = _lerp(CAP_H, max(CAP_H, lines_h + 2 * PAD_V), t)
        body_w = _lerp(CAP_W, self._open_w, t)
        x0 = (self.width() - (body_w + 2 * FLARE)) / 2
        left, right = x0 + FLARE, x0 + FLARE + body_w
        path = QPainterPath()
        path.moveTo(x0, 0)
        path.quadTo(left, 0, left, FLARE)
        path.lineTo(left, h - RADIUS)
        edge_x0, edge_x1 = left + RADIUS, right - RADIUS
        edge_w = edge_x1 - edge_x0
        amp, spatial = self._wave.amplitude, self._wave.spatial

        def edge_y(x: float, lag: float = 0.0) -> float:
            shift = wave_offset(x - edge_x0, edge_w, self._phase - lag, amp, spatial)
            return h + shift

        path.quadTo(left, h, edge_x0, h)
        x = edge_x0 + WAVE_STEP
        while x < edge_x1:
            path.lineTo(x, edge_y(x))
            x += WAVE_STEP
        path.lineTo(edge_x1, h)
        path.quadTo(right, h, right, h - RADIUS)
        path.lineTo(right, FLARE)
        path.quadTo(right, 0, right + FLARE, 0)
        path.closeSubpath()
        p.fillPath(path, self._body)
        line = QPainterPath()
        line.moveTo(edge_x0, h)
        x = edge_x0 + WAVE_STEP
        while x < edge_x1:
            gap = edge_gap(x - edge_x0, edge_w)
            line.lineTo(x, edge_y(x, WAVE_LAG) - gap)
            x += WAVE_STEP
        line.lineTo(edge_x1, h)
        line_color = QColor(self._text_color)
        line_color.setAlpha(70)
        pen = QPen(line_color, 1.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(line)

        t = self._expand
        dot_x = _lerp(self.width() / 2, left + DOT_LEFT, t)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        radius = 5 + 1.5 * self._pulse
        p.drawEllipse(QPointF(dot_x, h / 2), radius, radius)

        if self._text and t > 0.5:
            color = QColor(self._text_color)
            color.setAlpha(int(255 * min(1.0, (t - 0.5) * 2)))
            p.setPen(color)
            p.setFont(self._font)
            text_w = WRAP_W  # the layout width never changes, so the lines do not jump
            clip_w = body_w - TEXT_LEFT - TEXT_RIGHT
            top = (h - lines_h) / 2
            clip = QRectF(left + TEXT_LEFT, top, clip_w, lines_h)
            p.setClipRect(clip)
            flags = int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft)
            visible = self._text[: self._shown] if self._reveal else self._text
            full_h = self._full_h
            if self._reveal:
                full_h = (
                    QFontMetrics(self._font)
                    .boundingRect(0, 0, int(text_w), 10000, flags, visible)
                    .height()
                    if visible
                    else 0
                )
            # when the text is longer than two lines, the END stays visible
            y = top - self._scroll
            area = QRectF(left + TEXT_LEFT, y, text_w, max(full_h, lines_h))
            p.drawText(area, flags, visible)
        p.end()


class _Commands(QObject):
    state = Signal(str)
    theme = Signal(str)
    text = Signal(str)
    clear = Signal()
    reveal = Signal(str)
    chunk = Signal(int, int, float)
    done = Signal()
    quit_ = Signal()


def _read_stdin(commands: _Commands) -> None:
    """Reader thread: turns lines into signals; EOF means the parent is gone."""
    for line in sys.stdin:
        parts = line.strip().split(" ", 1)
        name = parts[0]
        if name == "state" and len(parts) == 2:
            commands.state.emit(parts[1])
        elif name == "theme" and len(parts) == 2:
            commands.theme.emit(parts[1])
        elif name == "text" and len(parts) == 2 and len(parts[1]) <= MAX_PAYLOAD:
            try:
                commands.text.emit(base64.b64decode(parts[1]).decode("utf-8"))
            except (binascii.Error, UnicodeDecodeError):
                pass
        elif name == "clear":
            commands.clear.emit()
        elif name == "reveal" and len(parts) == 2 and len(parts[1]) <= MAX_PAYLOAD:
            try:
                commands.reveal.emit(base64.b64decode(parts[1]).decode("utf-8"))
            except (binascii.Error, UnicodeDecodeError):
                pass
        elif name == "chunk" and len(parts) == 2:
            try:
                first, last, seconds = parts[1].split()
                commands.chunk.emit(int(first), int(last), float(seconds))
            except ValueError:
                pass
        elif name == "done":
            commands.done.emit()
        elif name == "quit":
            break
    commands.quit_.emit()


def main() -> None:
    app = QApplication(sys.argv)
    island = IslandWidget()
    screen = app.primaryScreen().geometry()
    island.set_screen(screen.x(), screen.y(), screen.width())
    island.show()

    commands = _Commands()
    commands.state.connect(island.set_state)
    commands.theme.connect(island.set_theme)
    commands.text.connect(island.show_text)
    commands.clear.connect(island.clear_text)
    commands.reveal.connect(island.start_reveal)
    commands.chunk.connect(island.reveal_chunk)
    commands.done.connect(island.finish_reveal)
    commands.quit_.connect(app.quit)
    threading.Thread(target=_read_stdin, args=(commands,), daemon=True).start()

    print("ready", flush=True)
    app.exec()


if __name__ == "__main__":
    main()
