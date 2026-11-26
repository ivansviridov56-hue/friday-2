"""Diagnostic probe: open the My Wave settings panel and press a mood button.

Usage (Yandex Music open on the My Wave page):
    python -m friday.ym_mood_press_probe                      # only report
    python -m friday.ym_mood_press_probe --open               # press "Настроить Мою волну"
    python -m friday.ym_mood_press_probe --mood Спокойное     # press a mood button

Presses ONLY what the flags ask for. Not part of the app.
"""

import argparse
import logging
import sys
import time

log = logging.getLogger("ym_mood_press_probe")

MOODS = ("Бодрое", "Весёлое", "Спокойное", "Грустное")
OPEN_NAME = "Настроить Мою волну"
CLOSE_NAME = "Закрыть меню настроек"
RESET_PREFIX = "Сбросить "
RESET_SUFFIX = " и включить Мою волну"
SETTLE_SECONDS = 1.5


def _find_window():
    from pywinauto import Desktop

    for window in Desktop(backend="uia").windows(visible_only=True):
        if "Яндекс Музыка" in (window.window_text() or ""):
            return window
    return None


def _norm(text: str) -> str:
    return (text or "").replace("\xa0", " ").strip()


def _buttons(window) -> dict[str, list]:
    """Visible (non-zero size) buttons by normalized name."""
    found: dict[str, list] = {}
    for button in window.descendants(control_type="Button"):
        try:
            rect = button.element_info.rectangle
            if rect.width() <= 0 or rect.height() <= 0:
                continue
            found.setdefault(_norm(button.element_info.name), []).append(button)
        except Exception:
            continue
    return found


def _state(button) -> str:
    parts = []
    for method in ("get_toggle_state", "is_selected"):
        try:
            parts.append(f"{method}={getattr(button, method)()}")
        except Exception:
            pass
    try:
        parts.append(f"legacy_state={button.legacy_properties().get('State')}")
    except Exception:
        pass
    return " ".join(parts) or "no state info"


def _report(window) -> None:
    buttons = _buttons(window)
    log.info("settings panel open: %s", CLOSE_NAME in buttons)
    log.info("open button visible: %s", OPEN_NAME in buttons)
    for mood in MOODS:
        for button in buttons.get(mood, []):
            log.info("mood %-10s %s", mood, _state(button))
        for button in _reset_buttons(window):
            log.info("reset button: %r", _norm(button.element_info.name))


def _press(button) -> None:
    try:
        button.invoke()
        log.info("pressed with invoke()")
    except Exception as exc:
        log.info(
            "invoke() failed (%s), falling back to click_input()", type(exc).__name__
        )
        button.click_input()


def _reset_buttons(window) -> list:
    """Buttons like 'Сбросить Весёлое и включить Мою волну' (names mood + reset)."""
    found = []
    for name, items in _buttons(window).items():
        if name.startswith(RESET_PREFIX) and name.endswith(RESET_SUFFIX):
            found.extend(items)
    return found


def _open_any(window) -> bool:
    """Press an 'open settings' button even if it is off screen (size 0 or scrolled away)."""
    candidates = [
        button
        for button in window.descendants(control_type="Button")
        if _norm(button.element_info.name) == OPEN_NAME
    ]
    log.info("open buttons in the tree: %d", len(candidates))
    for index, button in enumerate(candidates):
        try:
            rect = button.element_info.rectangle
            log.info("[%d] size %dx%d", index, rect.width(), rect.height())
            button.invoke()
            log.info("[%d] invoke() ok", index)
        except Exception as exc:
            log.info("[%d] invoke() failed: %s", index, type(exc).__name__)
            continue
        time.sleep(SETTLE_SECONDS)
        if CLOSE_NAME in _buttons(window):
            return True
        log.info("[%d] panel did not open", index)
    return False


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--mood", choices=MOODS, default=None)
    parser.add_argument("--open-any", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    try:
        window = _find_window()
    except ImportError:
        log.error("pywinauto is not installed in this environment")
        return 1
    if window is None:
        log.error("no visible Yandex Music window")
        return 1

    log.info("--- before ---")
    _report(window)
    buttons = _buttons(window)
    if args.open_any:
        opened = _open_any(window)
        log.info("panel open after --open-any: %s", opened)
        _report(window)
    if args.open:
        targets = buttons.get(OPEN_NAME, [])
        if not targets:
            log.error("no visible %r button", OPEN_NAME)
            return 1
        _press(targets[0])
        time.sleep(SETTLE_SECONDS)
        log.info("--- after --open ---")
        _report(window)
    if args.mood:
        targets = _buttons(window).get(args.mood, [])
        if len(targets) != 1:
            log.error(
                "expected one %r button, found %d (is the panel open?)",
                args.mood,
                len(targets),
            )
            return 1
        _press(targets[0])
        time.sleep(SETTLE_SECONDS)
        log.info("--- after --mood %s ---", args.mood)
        _report(window)
    if args.reset:
        targets = _reset_buttons(window)
        if len(targets) != 1:
            log.error("expected one reset button, found %d", len(targets))
            return 1
        _press(targets[0])
        time.sleep(SETTLE_SECONDS)
        log.info("--- after --reset ---")
        _report(window)
    return 0


if __name__ == "__main__":
    sys.exit(main())
