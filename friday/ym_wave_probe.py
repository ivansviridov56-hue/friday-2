"""Probe: find the "My Wave" start control on the Yandex Music home page.

Open the home page with My Wave visible, then:
    python -m friday.ym_wave_probe            # list controls related to the wave
    python -m friday.ym_wave_probe --tree 1   # structure around candidate #1

Live-checked tool, no unit tests. Read-only: it never clicks anything.
"""

from __future__ import annotations

import sys

from friday.ym_ui_probe import find_window, lineage, tree

# "волн" written as escapes so the file survives any console encoding
WORDS = ("\u0432\u043e\u043b\u043d", "wave")


def wave_candidates(window) -> list:
    found = []
    try:
        elements = window.descendants()
    except Exception:
        return found
    for element in elements:
        try:
            name = (element.window_text() or "").strip().lower()
            auto_id = (element.element_info.automation_id or "").lower()
            visible = element.rectangle().width() > 0
        except Exception:
            continue
        if visible and any(w in name or w in auto_id for w in WORDS):
            found.append(element)
    return found


def main(args: list[str]) -> None:
    window = find_window()
    if window is None:
        print("Yandex Music window not found")
        return
    items = wave_candidates(window)
    print(f"{len(items)} candidates")
    for index, element in enumerate(items, 1):
        r = element.rectangle()
        print(
            f"#{index} {element.element_info.control_type} "
            f"{(element.window_text() or '')[:60]!r} "
            f"id={element.element_info.automation_id!r} "
            f"{r.width()}x{r.height()} in {lineage(element)}"
        )
    if len(args) == 2 and args[0] == "--tree":
        number = int(args[1])
        if not 1 <= number <= len(items):
            print(f"No candidate #{number}")
            return
        tree(items[number - 1].parent().parent())


if __name__ == "__main__":
    main(sys.argv[1:])
