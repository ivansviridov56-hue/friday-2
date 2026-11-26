"""Probe: the island as a Qt Quick window (GPU scene graph; not wired into the app).

Run: python -m friday.island_quick_probe
Closes by itself after 60 s, or press Ctrl+C in the console.
"""

from __future__ import annotations

import signal
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import QColor, QGuiApplication, QSurfaceFormat
from PySide6.QtQuick import QQuickView

WIDTH, HEIGHT = 480, 90

QML = r"""
import QtQuick
import QtQuick.Shapes

Item {
    id: root
    width: 480; height: 90
    clip: true
    property real t: 0
    property real phase: 0
    property real openP: 0
    property real e: 0
    property real bodyW: 150
    property real bodyH: 34

    FrameAnimation {
        running: true
        onTriggered: {
            root.t += frameTime
            root.phase += frameTime * 1.2
            var T = root.t % 12
            var open = T > 1 && T < 9
            root.openP = Math.max(0, Math.min(1, root.openP + (open ? 1 : -1) * frameTime / 0.45))
            root.e = root.openP * root.openP * (3 - 2 * root.openP)
            root.bodyW = 150 + 290 * root.e
            root.bodyH = 34 + 20 * root.e
            var left = (root.width - root.bodyW) / 2
            var R = 14
            var right = left + root.bodyW
            var cy = root.bodyH - R
            var pts = [Qt.point(left, -2), Qt.point(left, cy)]
            for (var k = 1; k <= 6; k++) {
                var a = Math.PI - (Math.PI / 2) * k / 6
                pts.push(Qt.point(left + R + R * Math.cos(a), cy + R * Math.sin(a)))
            }
            var x0 = left + R, x1 = right - R
            for (var x = x0 + 3; x < x1; x += 3) {
                var u = (x - x0) / (x1 - x0)
                pts.push(Qt.point(x, root.bodyH + 3 * Math.sin(Math.PI * u) * Math.sin(u * 9.4 + root.phase)))
            }
            for (var m = 0; m <= 6; m++) {
                var b = (Math.PI / 2) - (Math.PI / 2) * m / 6
                pts.push(Qt.point(right - R + R * Math.cos(b), cy + R * Math.sin(b)))
            }
            pts.push(Qt.point(right, -2))
            poly.path = pts
        }
    }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.GeometryRenderer
        layer.enabled: true
        layer.samples: 4
        ShapePath {
            fillColor: "#202020"
            strokeColor: "transparent"
            PathPolyline { id: poly; path: [] }
        }
    }

    Rectangle {
        width: 10; height: 10; radius: 5; color: "#3aa6d8"
        x: root.width / 2 - 5 + (-(root.bodyW / 2) + 27 + 5 - 0) * root.e
        y: root.bodyH / 2 - 5
    }

    Text {
        x: (root.width - root.bodyW) / 2 + 40
        y: (root.bodyH - height) / 2
        width: root.bodyW - 58
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        elide: Text.ElideRight
        color: "#e8e8e8"
        font.pixelSize: 13
        opacity: Math.max(0, (root.e - 0.5) * 2)
        text: "Привет, босс. Расскажу про космос: он большой, холодный и очень тихий."
    }
}
"""


def main() -> None:
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)
    app = QGuiApplication(sys.argv)

    qml = Path(tempfile.gettempdir()) / "island_quick_probe.qml"
    qml.write_text(QML, encoding="utf-8")

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
    view.setSource(QUrl.fromLocalFile(str(qml)))
    screen = app.primaryScreen().geometry()
    view.setGeometry(
        screen.x() + (screen.width() - WIDTH) // 2, screen.y(), WIDTH, HEIGHT
    )
    view.show()

    frames = [0]
    view.frameSwapped.connect(lambda: frames.__setitem__(0, frames[0] + 1))

    def report() -> None:
        print(f"island quick fps: {frames[0]}", flush=True)
        frames[0] = 0

    counter = QTimer()
    counter.timeout.connect(report)
    counter.start(1000)
    QTimer.singleShot(
        1500,
        lambda: print(
            "graphics api:", view.rendererInterface().graphicsApi(), flush=True
        ),
    )

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    keepalive = QTimer()  # lets Python see Ctrl+C while Qt is running
    keepalive.timeout.connect(lambda: None)
    keepalive.start(200)
    QTimer.singleShot(60_000, app.quit)
    for err in view.errors():
        print("QML error:", err.toString(), flush=True)
    app.exec()


if __name__ == "__main__":
    main()
