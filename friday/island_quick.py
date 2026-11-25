"""The island as a Qt Quick window (stage 28b). Runs as its own process.

Run: python -m friday.island_quick
Commands arrive on stdin, one per line, like in friday.island_qt: "state <name>",
"theme <name>", "text <base64>", "clear", "reveal <base64>", "chunk <first> <last> <seconds>",
"done" or "quit". The process prints "ready" once the window is shown and exits when stdin
closes. The animation lives in IslandModel and the outline in island_shape; this file only
moves data between them and the page friday/ui/island.qml. Live-checked, no unit tests.
"""

from __future__ import annotations

import base64
import binascii
import math
import os
import signal
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QObject,
    QPointF,
    QRectF,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QGuiApplication,
    QSurfaceFormat,
)
from PySide6.QtQuick import QQuickView

from friday.island_logic import WAVE_PAD
from friday.island_model import (
    CAP_H,
    EXP_W,
    MAX_LINES,
    PAD_V,
    TEXT_LEFT,
    TEXT_RIGHT,
    WRAP_W,
    IslandModel,
)
from friday.island_shape import FLARE, body_outline, light_line

ROOT = Path(__file__).resolve().parent.parent
QML_PATH = ROOT / "friday" / "ui" / "island.qml"
FPS_LOG = ROOT / "data" / "island_fps.txt"
WINDOW_W = EXP_W + 2 * FLARE
DOT_LEFT = 22  # dot position (from the body's left edge) when expanded
FONT_PX = 13
FONT_FAMILIES = ["Rubik", "Segoe UI", "sans-serif"]
MAX_PAYLOAD = 8000  # base64 characters accepted per text command


def pick_family() -> str:
    """The first installed font of the list; the page takes one name only."""
    installed = set(QFontDatabase.families())
    for name in FONT_FAMILIES:
        if name in installed:
            return name
    return "Segoe UI"


class IslandBackend(QObject):
    """Holds the model; the page reads its properties after every frame."""

    changed = Signal()

    def __init__(self, font: QFont) -> None:
        super().__init__()
        self._family = font.family()
        metrics = QFontMetricsF(font)
        flags = int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft)

        def measure(text: str) -> tuple[float, float]:
            rect = metrics.boundingRect(QRectF(0, 0, WRAP_W, 10000), flags, text)
            return rect.width(), rect.height()

        line_h = metrics.lineSpacing()
        self._model = IslandModel(measure, line_h)
        self._height = math.ceil(max(CAP_H, line_h * MAX_LINES + 2 * PAD_V)) + WAVE_PAD
        self._outline: list[QPointF] = []
        self._line: list[QPointF] = []
        self._publish()

    def window_height(self) -> int:
        return self._height

    def _publish(self) -> None:
        m = self._model
        args = (WINDOW_W, m.body_w, m.body_h, m.wave_amplitude, m.wave_spatial, m.phase)
        self._outline = [QPointF(x, y) for x, y in body_outline(*args)]
        self._line = [QPointF(x, y) for x, y in light_line(*args)]
        self.changed.emit()

    # ---- called by the page ----
    @Slot(float)
    def frame(self, dt: float) -> None:
        self._model.tick(dt, time.monotonic())
        self._publish()

    # ---- commands from stdin ----
    def set_state(self, state: str) -> None:
        self._model.set_state(state)

    def set_theme(self, theme: str) -> None:
        self._model.set_theme(theme)

    def show_text(self, text: str) -> None:
        self._model.show_text(text)

    def clear_text(self) -> None:
        self._model.clear_text()

    def start_reveal(self, text: str) -> None:
        self._model.start_reveal(text)

    def reveal_chunk(self, first: int, last: int, seconds: float) -> None:
        self._model.reveal_chunk(first, last, seconds, time.monotonic())

    def finish_reveal(self) -> None:
        self._model.finish_reveal()

    # ---- properties read by the page (names are camelCase on purpose) ----
    @Property(int, constant=True)
    def windowW(self) -> int:  # noqa: N802
        return WINDOW_W

    @Property(int, constant=True)
    def windowH(self) -> int:  # noqa: N802
        return self._height

    @Property(str, constant=True)
    def fontFamily(self) -> str:  # noqa: N802
        return self._family

    @Property(int, constant=True)
    def textLeft(self) -> int:  # noqa: N802
        return TEXT_LEFT

    @Property(int, constant=True)
    def textRight(self) -> int:  # noqa: N802
        return TEXT_RIGHT

    @Property(int, constant=True)
    def wrapW(self) -> int:  # noqa: N802
        return WRAP_W

    @Property("QVariantList", notify=changed)  # type: ignore[arg-type]
    def outline(self) -> list:
        return self._outline

    @Property("QVariantList", notify=changed)  # type: ignore[arg-type]
    def lightLine(self) -> list:  # noqa: N802
        return self._line

    @Property(float, notify=changed)
    def bodyW(self) -> float:  # noqa: N802
        return self._model.body_w

    @Property(float, notify=changed)
    def bodyH(self) -> float:  # noqa: N802
        return self._model.body_h

    @Property(float, notify=changed)
    def linesH(self) -> float:  # noqa: N802
        return self._model.lines_h

    @Property(float, notify=changed)
    def scroll(self) -> float:
        return self._model.scroll

    @Property(float, notify=changed)
    def pulse(self) -> float:
        return self._model.pulse

    @Property(float, notify=changed)
    def textAlpha(self) -> float:  # noqa: N802
        return self._model.text_alpha

    @Property(float, notify=changed)
    def dotX(self) -> float:  # noqa: N802
        m = self._model
        left = (WINDOW_W - m.body_w) / 2
        return WINDOW_W / 2 + (left + DOT_LEFT - WINDOW_W / 2) * m.expand

    @Property(str, notify=changed)
    def visibleText(self) -> str:  # noqa: N802
        return self._model.visible_text

    @Property(str, notify=changed)
    def dotColor(self) -> str:  # noqa: N802
        return self._model.dot_color

    @Property(str, notify=changed)
    def bodyColor(self) -> str:  # noqa: N802
        return self._model.body_color

    @Property(str, notify=changed)
    def textColor(self) -> str:  # noqa: N802
        return self._model.text_color

    @Property(str, notify=changed)
    def lineColor(self) -> str:  # noqa: N802
        color = QColor(self._model.text_color)
        color.setAlpha(70)
        return color.name(QColor.NameFormat.HexArgb)


class _Commands(QObject):
    state = Signal(str)
    theme = Signal(str)
    text = Signal(str)
    clear = Signal()
    reveal = Signal(str)
    chunk = Signal(int, int, float)
    done = Signal()
    quit_ = Signal()


def _decode(payload: str) -> str | None:
    if len(payload) > MAX_PAYLOAD:
        return None
    try:
        return base64.b64decode(payload).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None


def _read_stdin(commands: _Commands) -> None:
    """Reader thread: turns lines into signals; EOF means the parent is gone."""
    for line in sys.stdin:
        parts = line.strip().split(" ", 1)
        name = parts[0]
        arg = parts[1] if len(parts) == 2 else ""
        if name == "state" and arg:
            commands.state.emit(arg)
        elif name == "theme" and arg:
            commands.theme.emit(arg)
        elif name in ("text", "reveal") and arg:
            text = _decode(arg)
            if text is not None:
                (commands.text if name == "text" else commands.reveal).emit(text)
        elif name == "clear":
            commands.clear.emit()
        elif name == "chunk" and arg:
            try:
                first, last, seconds = arg.split()
                commands.chunk.emit(int(first), int(last), float(seconds))
            except ValueError:
                pass
        elif name == "done":
            commands.done.emit()
        elif name == "quit":
            break
    commands.quit_.emit()


def _count_frames(view: QQuickView) -> QTimer | None:
    """With FRIDAY_ISLAND_FPS=1 the frames that really reached the screen are counted."""
    if os.environ.get("FRIDAY_ISLAND_FPS") != "1":
        return None
    frames = [0]
    view.frameSwapped.connect(lambda: frames.__setitem__(0, frames[0] + 1))

    def write() -> None:
        FPS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(FPS_LOG, "a", encoding="utf-8") as f:
            f.write(f"island quick fps: {frames[0]}\n")
        frames[0] = 0

    timer = QTimer(view)
    timer.timeout.connect(write)
    timer.start(1000)
    return timer


def main() -> None:
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)
    app = QGuiApplication(sys.argv)

    font = QFont()
    font.setFamily(pick_family())
    font.setPixelSize(FONT_PX)
    backend = IslandBackend(font)

    view = QQuickView()
    view.setFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.Tool
        | Qt.WindowType.WindowDoesNotAcceptFocus
        | Qt.WindowType.WindowTransparentForInput
    )
    view.setColor(QColor(0, 0, 0, 0))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.rootContext().setContextProperty("backend", backend)
    view.setSource(QUrl.fromLocalFile(str(QML_PATH)))
    if view.status() == QQuickView.Status.Error:
        for err in view.errors():
            print("island QML error:", err.toString(), file=sys.stderr, flush=True)
        sys.exit(1)

    screen = app.primaryScreen().geometry()
    x = screen.x() + (screen.width() - WINDOW_W) // 2
    view.setGeometry(x, screen.y(), WINDOW_W, backend.window_height())
    view.show()
    fps_timer = _count_frames(view)

    commands = _Commands()
    commands.state.connect(backend.set_state)
    commands.theme.connect(backend.set_theme)
    commands.text.connect(backend.show_text)
    commands.clear.connect(backend.clear_text)
    commands.reveal.connect(backend.start_reveal)
    commands.chunk.connect(backend.reveal_chunk)
    commands.done.connect(backend.finish_reveal)
    commands.quit_.connect(app.quit)
    threading.Thread(target=_read_stdin, args=(commands,), daemon=True).start()

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    keepalive = QTimer()  # lets Python see Ctrl+C while Qt is running
    keepalive.timeout.connect(lambda: None)
    keepalive.start(200)

    print("ready", flush=True)
    app.exec()
    del fps_timer


if __name__ == "__main__":
    main()
