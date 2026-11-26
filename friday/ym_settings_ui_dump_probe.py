"""Diagnostic probe: dump the Yandex Music window controls (names, types, sizes).

Usage:
    1. Open Yandex Music, open My Wave, open its settings panel by hand.
    2. python -m friday.ym_settings_ui_dump_probe

Read-only: nothing is pressed. Writes data/probes/ym_ui_dump.txt (git-ignored).
The dump may contain the track and artist that are shown, nothing else.
"""

import logging
import sys
import time
from pathlib import Path

log = logging.getLogger("ym_settings_ui_dump_probe")

MAX_DEPTH = 14
MAX_NODES = 2500
OUT = Path(__file__).resolve().parent.parent / "data" / "probes" / "ym_ui_dump.txt"


def _find_window():
    from pywinauto import Desktop

    for window in Desktop(backend="uia").windows(visible_only=True):
        if "Яндекс Музыка" in (window.window_text() or ""):
            return window
    return None


def _walk(element, depth: int, lines: list[str]) -> None:
    if depth > MAX_DEPTH or len(lines) >= MAX_NODES:
        return
    try:
        info = element.element_info
        rect = info.rectangle
        name = (info.name or "").replace("\n", " ")[:60]
        lines.append(
            f"{'  ' * depth}{info.control_type} | {name!r} | "
            f"{rect.width()}x{rect.height()} @({rect.left},{rect.top})"
        )
        children = element.children()
    except Exception as exc:  # a control can vanish while walking
        lines.append(f"{'  ' * depth}<error: {type(exc).__name__}>")
        return
    for child in children:
        _walk(child, depth + 1, lines)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        window = _find_window()
    except ImportError:
        log.error("pywinauto is not installed in this environment")
        return 1
    if window is None:
        log.error("no visible Yandex Music window (is it minimized or closed?)")
        return 1
    lines: list[str] = []
    for attempt in range(1, 5):
        lines = []
        _walk(window, 0, lines)
        log.info("attempt %d: %d controls", attempt, len(lines))
        if len(lines) > 40:
            break
        time.sleep(3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    log.info("controls written: %d, file: %s", len(lines), OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
