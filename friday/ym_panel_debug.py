"""Debug: why does find_panel() return nothing? Open the track page first."""

from __future__ import annotations

import time

from friday.ym_ui import (
    CLOSE_NAME,
    MAX_LEVELS,
    PLAY_NAME,
    _descendants,
    _find_window,
    _label,
    _title_after_mark,
    find_panel,
)


def main() -> None:
    window = _find_window()
    if window is None:
        print("window not found")
        return
    plays = [
        b for b in _descendants(window, "Button") if _label(b).lower() == PLAY_NAME
    ]
    print("play buttons:", len(plays))
    for number, button in enumerate(plays, 1):
        rect = button.rectangle()
        parts = [f"#{number} ({rect.left},{rect.top})"]
        node = button
        for level in range(1, MAX_LEVELS + 1):
            node = node.parent()
            if node is None:
                parts.append(f"L{level}:none")
                break
            buttons = _descendants(node, "Button")
            n_play = sum(_label(b).lower() == PLAY_NAME for b in buttons)
            has_close = any(_label(b).lower() == CLOSE_NAME for b in buttons)
            title = _title_after_mark(node)
            parts.append(
                f"L{level}:{node.element_info.control_type} p={n_play} c={int(has_close)} t={title!r}"
            )
        print(" | ".join(parts))

    started = time.monotonic()
    panel = find_panel()
    took = time.monotonic() - started
    print("find_panel:", None if panel is None else repr(panel.title), f"({took:.1f}s)")


if __name__ == "__main__":
    main()
