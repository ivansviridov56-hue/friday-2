"""Diagnostic probe: find My Wave cards anywhere in the Yandex Music UI tree.

Usage:
    1. Open Yandex Music on the My Wave page.
    2. python -m friday.ym_wave_cards_scan_probe

Read-only: nothing is pressed. Searches the whole window, not one region, and
prints how many nodes it walked and whether the walk was cut by a limit.
The dump may contain card titles and artist names that are shown, nothing else.
"""

import logging
import sys

from friday.ym_settings_ui_dump_probe import _find_window


def _children(element) -> list:
    try:
        return element.children()
    except Exception:  # a control can vanish while walking
        return []


def _info(element):
    try:
        return element.element_info
    except Exception:
        return None


log = logging.getLogger("ym_wave_cards_scan_probe")

PREFIXES = ("моя волна", "сингл")
MAX_DEPTH = 22
MAX_NODES = 8000


def _norm(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").lower().split())


def _walk(element, depth: int, rows: list[str], stats: dict) -> None:
    if depth > MAX_DEPTH or stats["nodes"] >= MAX_NODES:
        stats["cut"] = True
        return
    stats["nodes"] += 1
    info = _info(element)
    if info is None:
        return
    if info.control_type == "ListItem":
        stats["list_items"] += 1
    name = _norm(info.name or "")
    if info.control_type in ("Group", "Button") and name.startswith(PREFIXES):
        rect = info.rectangle
        rows.append(
            f"d={depth} {info.control_type} {info.name!r} "
            f"{rect.width()}x{rect.height()} @({rect.left},{rect.top})"
        )
    for child in _children(element):
        _walk(child, depth + 1, rows, stats)


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
    rows: list[str] = []
    stats = {"nodes": 0, "list_items": 0, "cut": False}
    _walk(window, 0, rows, stats)
    log.info("\n".join(rows))
    log.info(
        "cards: %d, list items: %d, nodes walked: %d, cut by limit: %s",
        len(rows),
        stats["list_items"],
        stats["nodes"],
        stats["cut"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
