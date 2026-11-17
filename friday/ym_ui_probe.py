"""Probe: what can UI Automation see in the Yandex Music window?

Open a track page in the app (e.g. with friday.ym_open_probe), then:
    python -m friday.ym_ui_probe            # list "play" buttons with their surroundings
    python -m friday.ym_ui_probe --click 1  # invoke candidate #1 and show what plays

Live-checked tool, no unit tests.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys

from pywinauto import Application

from friday.ym_open_probe import describe

EXE_NAMES = ("Яндекс Музыка.exe", "YandexMusic.exe")
WORDS = ("слуша", "воспроизвед", "play")
TYPES = ("Button", "Hyperlink", "Custom")


def _pids() -> list[int]:
    pids: list[int] = []
    for exe in EXE_NAMES:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
            ).decode("cp866", errors="ignore")
        except Exception:
            continue
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.strip().split(",")]
            if len(parts) > 1 and parts[1].isdigit():
                pids.append(int(parts[1]))
    return pids


def find_window():
    for pid in _pids():
        try:
            app = Application(backend="uia").connect(process=pid)
            windows = app.windows(visible_only=True)
        except Exception:
            continue
        if windows:
            titled = [w for w in windows if (w.window_text() or "").strip()]
            return (titled or windows)[0]
    return None


def candidates(window) -> list:
    found = []
    for control_type in TYPES:
        try:
            elements = window.descendants(control_type=control_type)
        except Exception:
            continue
        for element in elements:
            try:
                name = (element.window_text() or "").strip().lower()
                visible = element.rectangle().width() > 0
            except Exception:
                continue
            if visible and any(word in name for word in WORDS):
                found.append(element)
    return found


def lineage(element) -> str:
    parts = []
    node = element
    for _ in range(3):
        try:
            node = node.parent()
            kind = node.element_info.control_type
            parts.append(f"{kind}:{(node.window_text() or '')[:25]!r}")
        except Exception:
            break
    return " < ".join(parts)


def tree(element, depth: int = 0, max_depth: int = 3) -> None:
    try:
        kind = element.element_info.control_type
        name = (element.window_text() or "")[:40]
        r = element.rectangle()
        children = element.children()
    except Exception:
        return
    print(f"{'  ' * depth}{kind} {name!r} {r.width()}x{r.height()}")
    if depth < max_depth:
        for child in children:
            tree(child, depth + 1, max_depth)


async def main(mode: str, number: int | None) -> None:
    window = find_window()
    if window is None:
        print("Yandex Music window not found")
        return
    items = candidates(window)
    print(f"{len(items)} candidates")
    for index, element in enumerate(items, 1):
        r = element.rectangle()
        print(
            f"#{index} {element.element_info.control_type} "
            f"{element.window_text()!r} id={element.element_info.automation_id!r} "
            f"rect=({r.left},{r.top},{r.right},{r.bottom}) in {lineage(element)}"
        )
    if number is None:
        return
    if not 1 <= number <= len(items):
        print(f"No candidate #{number}")
        return
    target = items[number - 1]
    if mode == "--tree":
        # two levels up: the group that holds the whole track panel
        tree(target.parent().parent())
        return
    print("before:", await describe())
    try:
        target.invoke()
        print("invoked (no mouse movement)")
    except Exception:
        print("invoke failed, using a real mouse click")
        target.click_input()
    await asyncio.sleep(3)
    print("after: ", await describe())


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = args[0] if args else ""
    number = int(args[1]) if len(args) > 1 else None
    asyncio.run(main(mode, number))
