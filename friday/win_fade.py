"""Sets the opacity of the whole window. Live-checked, no unit tests."""

from __future__ import annotations


class FormOpacity:
    def __init__(self, window: object) -> None:
        self._window = window

    def __call__(self, value: float) -> None:
        """Any thread; the form is changed on the interface thread."""
        from System import Action  # type: ignore[import-not-found]

        form = self._window.native  # type: ignore[attr-defined]

        def apply() -> None:
            form.Opacity = value

        form.Invoke(Action(apply))
