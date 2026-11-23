"""Desktop window (PyWebView). Glue only; checked live, no unit tests.

`python -m friday.window` opens the window with a short demo dialogue.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from friday.backdrop_tint import BackdropTint
from friday.text_input import TextInput
from friday.window_api import WindowApi
from friday.window_controls import WindowControls
from friday.ui_bridge import UiBridge
from friday.ui_events import (
    CirclesStyleChanged,
    MessageAdded,
    State,
    StateChanged,
    ThemeChanged,
    UiEventBus,
)

logger = logging.getLogger(__name__)

HTML_PATH = Path(__file__).resolve().parent / "ui" / "index.html"

TITLE = "Пятница"


def run_window(
    bus: UiEventBus,
    api: WindowApi | None = None,
    controls: WindowControls | None = None,
) -> None:
    """Show the window and block until it is closed. Must run on the main thread."""
    import webview
    from friday.win_backdrop import Backdrop

    window = webview.create_window(
        TITLE,
        url=str(HTML_PATH),
        width=1000,
        height=640,
        background_color="#14161a",
        js_api=api,
        frameless=True,
        easy_drag=False,
        transparent=True,
    )
    if window is None:
        raise RuntimeError("could not create the window")
    if controls is not None:
        controls.bind(window.minimize, window.destroy, window.resize)
    bridge = UiBridge(window.evaluate_js)
    bus.subscribe(bridge.on_event)
    backdrop = Backdrop(window, TITLE)
    tint = BackdropTint(backdrop.set_tint)
    bus.subscribe(tint.on_event)
    window.events.loaded += bridge.mark_ready
    window.events.loaded += backdrop.start
    try:
        webview.start()
    finally:
        bus.unsubscribe(bridge.on_event)
        bus.unsubscribe(tint.on_event)
        if controls is not None:
            controls.unbind()


def _demo(bus: UiEventBus) -> None:
    time.sleep(1.5)
    bus.publish(StateChanged(State.LISTENING))
    time.sleep(1.5)
    bus.publish(StateChanged(State.THINKING))
    bus.publish(MessageAdded("user", "Привет, как дела?"))
    time.sleep(1.5)
    bus.publish(MessageAdded("assistant", "Привет! Всё хорошо, а у тебя?"))
    bus.publish(StateChanged(State.SPEAKING))
    time.sleep(2)
    bus.publish(StateChanged(State.IDLE))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bus = UiEventBus()
    bus.publish(CirclesStyleChanged("classic"))
    bus.publish(ThemeChanged("classic"))
    threading.Thread(target=_demo, args=(bus,), daemon=True).start()
    controls = WindowControls()
    run_window(bus, WindowApi(TextInput(), controls), controls)


if __name__ == "__main__":
    main()
