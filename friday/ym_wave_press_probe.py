"""Probe: press Play in the My Wave player block, found by structure.

Open the Yandex Music home page, then:
    python -m friday.ym_wave_press_probe          # only show what would be pressed
    python -m friday.ym_wave_press_probe --press  # invoke it and show what plays

Live-checked tool, no unit tests.
"""

from __future__ import annotations

import asyncio
import sys

from friday.ym_open_probe import describe
from friday.ym_ui_probe import find_window


def player_groups(window) -> list:
    """Groups with two sliders and 3+ buttons: (group, buttons)."""
    found = []
    try:
        groups = window.descendants(control_type="Group")
    except Exception:
        return found
    for group in groups:
        try:
            kids = group.children()
            sliders = [k for k in kids if k.element_info.control_type == "Slider"]
            buttons = [k for k in kids if k.element_info.control_type == "Button"]
            visible = group.rectangle().width() > 0
        except Exception:
            continue
        if visible and len(sliders) == 2 and len(buttons) >= 3:
            found.append((group, buttons))
    return found


async def main(press: bool) -> None:
    window = find_window()
    if window is None:
        print("Yandex Music window not found")
        return
    groups = player_groups(window)
    print(f"{len(groups)} player groups")
    for index, (group, buttons) in enumerate(groups, 1):
        r = group.rectangle()
        names = [(b.window_text() or "")[:25] for b in buttons[-3:]]
        print(
            f"#{index} at ({r.left},{r.top}) {r.width()}x{r.height()} last 3 buttons: {names}"
        )
    if not press:
        return
    if len(groups) != 1:
        print("Expected exactly one player group, not pressing")
        return
    target = groups[0][1][-3:][1]
    print("before:", await describe())
    target.invoke()
    print("invoked (no mouse movement)")
    await asyncio.sleep(3)
    print("after: ", await describe())


if __name__ == "__main__":
    asyncio.run(main("--press" in sys.argv[1:]))
