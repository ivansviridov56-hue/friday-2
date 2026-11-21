"""Methods the page can call as window.pywebview.api.<name>(...).

Keep this class thin: every public method is reachable from the page, so it only
forwards to other modules. Attributes start with an underscore on purpose (PyWebView
does not expose those).
"""

from __future__ import annotations

import math

from friday.text_input import TextInput
from friday.window_controls import WindowControls


def _is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


class WindowApi:
    def __init__(self, text_input: TextInput, controls: WindowControls) -> None:
        self._text_input = text_input
        self._controls = controls

    def submit_text(self, text: object) -> bool:
        if not isinstance(text, str):
            return False
        return self._text_input.submit(text)

    def minimize_window(self) -> bool:
        return self._controls.minimize()

    def close_window(self) -> bool:
        return self._controls.close()

    def resize_window(self, width: object, height: object) -> bool:
        if not (_is_number(width) and _is_number(height)):
            return False
        return self._controls.resize(float(width), float(height))  # type: ignore[arg-type]
