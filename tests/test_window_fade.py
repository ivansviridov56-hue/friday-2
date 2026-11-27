"""The window fades in and out; a newer request takes over from the older one."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from friday.window_fade import FADE_SECONDS, FRAME, WindowFade


class Rig:
    """Fake window and fake time. Jobs run only when run() is called."""

    def __init__(self, fail: str = "") -> None:
        self.events: list[object] = []
        self.jobs: list[Callable[[], None]] = []
        self.now = 0.0
        self.fail = fail
        self.on_sleep: Callable[[], None] | None = None
        self.fade = WindowFade(
            self._opacity,
            lambda: self._call("show"),
            lambda: self._call("hide"),
            spawn=self.jobs.append,
            clock=lambda: self.now,
            sleep=self._sleep,
        )

    def _opacity(self, value: float) -> None:
        if self.fail == "opacity" and 0.0 < value < 1.0:
            raise OSError("boom")
        self.events.append(value)

    def _call(self, name: str) -> None:
        if self.fail == name:
            raise OSError("boom")
        self.events.append(name)

    def _sleep(self, seconds: float) -> None:
        self.now += seconds
        if self.on_sleep is not None:
            self.on_sleep()

    def run(self) -> None:
        while self.jobs:
            self.jobs.pop(0)()

    def levels(self) -> list[float]:
        return [e for e in self.events if isinstance(e, float)]


def test_hide_returns_before_anything_happens() -> None:
    rig = Rig()
    rig.fade.hide()
    assert rig.events == []
    assert len(rig.jobs) == 1


def test_hide_fades_out_and_then_hides() -> None:
    rig = Rig()
    rig.fade.hide()
    rig.run()
    assert rig.events[-1] == "hide"
    levels = rig.levels()
    assert levels == sorted(levels, reverse=True)
    assert levels[-1] == 0.0
    assert len(levels) > 10


def test_fade_takes_about_the_set_time() -> None:
    rig = Rig()
    rig.fade.hide()
    rig.run()
    assert FADE_SECONDS <= rig.now <= FADE_SECONDS + 2 * FRAME


def test_show_after_hide_shows_first_and_then_fades_in() -> None:
    rig = Rig()
    rig.fade.hide()
    rig.run()
    rig.events.clear()
    rig.fade.show()
    rig.run()
    assert rig.events[0] == "show"
    levels = rig.levels()
    assert levels == sorted(levels)
    assert levels[-1] == 1.0


def test_show_of_a_visible_window_does_not_blink() -> None:
    rig = Rig()
    rig.fade.show()
    rig.run()
    assert rig.events == ["show", 1.0]


def test_show_during_a_fade_out_takes_over_without_hiding() -> None:
    rig = Rig()

    def reopen() -> None:
        if rig.now > FADE_SECONDS / 4:
            rig.on_sleep = None
            rig.fade.show()

    rig.on_sleep = reopen
    rig.fade.hide()
    rig.run()
    assert "hide" not in rig.events
    tail = rig.events[rig.events.index("show") + 1 :]
    after = [e for e in tail if isinstance(e, float)]
    assert after[0] > 0.0  # continues from where it was
    assert after[-1] == 1.0


def test_an_outdated_request_does_nothing() -> None:
    rig = Rig()
    rig.fade.hide()
    rig.fade.show()
    rig.run()
    assert rig.events == ["show", 1.0]


def test_appear_makes_transparent_before_uncloaking() -> None:
    rig = Rig()

    def uncloak() -> bool:
        rig.events.append("uncloak")
        return True

    assert rig.fade.appear(uncloak) is True
    assert rig.events == [0.0, "uncloak"]
    rig.run()
    assert rig.levels()[-1] == 1.0


def test_appear_with_failed_uncloak_stays_opaque() -> None:
    rig = Rig()
    assert rig.fade.appear(lambda: False) is False
    assert rig.events == [0.0, 1.0]
    assert rig.jobs == []


def test_failed_hide_restores_the_window_and_the_next_one_raises() -> None:
    rig = Rig(fail="hide")
    rig.fade.hide()
    rig.run()
    assert rig.levels()[-1] == 1.0
    with pytest.raises(RuntimeError):
        rig.fade.hide()


def test_failed_show_still_leaves_the_window_opaque() -> None:
    rig = Rig(fail="show")
    rig.fade.show()
    rig.run()
    assert rig.levels()[-1] == 1.0


def test_broken_opacity_still_hides_the_window() -> None:
    rig = Rig(fail="opacity")
    rig.fade.hide()
    rig.run()
    assert rig.events[-1] == "hide"


def test_close_stops_pending_work() -> None:
    rig = Rig()
    rig.fade.hide()
    rig.fade.close()
    rig.run()
    assert rig.events == []
