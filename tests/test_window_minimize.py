"""Minimizing: fade and slide down, minimize, and rise again when restored."""

from __future__ import annotations

from collections.abc import Callable

from friday.window_fade import MINIMIZE_TIMEOUT, SHIFT, WindowFade

HOME = (100, 200)


class FakeWindow:
    def __init__(self, fail: str = "") -> None:
        self.fail = fail
        self.place = HOME
        self.opacity = 1.0
        self.minimized = False
        self.hidden = False
        self.minimize_calls = 0
        self.moves: list[int] = []
        self.opacity_at_minimize: float | None = None
        self.place_at_minimize: tuple[int, int] | None = None

    def position(self) -> tuple[int, int]:
        return self.place

    def move(self, x: int, y: int) -> None:
        assert not self.minimized, "a minimized window must not be moved"
        self.place = (x, y)
        self.moves.append(y)

    def minimize(self) -> None:
        self.minimize_calls += 1
        if self.fail == "raises":
            raise OSError("boom")
        if self.fail != "ignored":
            self.opacity_at_minimize = self.opacity
            self.place_at_minimize = self.place
            self.minimized = True

    def restore(self) -> None:
        self.minimized = False

    def is_minimized(self) -> bool:
        return self.minimized


class Rig:
    """Fake time; `at` runs an action once the condition is true during a sleep."""

    def __init__(self, fail: str = "") -> None:
        self.window = FakeWindow(fail)
        self.jobs: list[Callable[[], None]] = []
        self.now = 0.0
        self.hooks: list[tuple[Callable[[], bool], Callable[[], object]]] = []
        self.fade = WindowFade(
            self._opacity,
            self._show,
            self._hide,
            spawn=self.jobs.append,
            clock=lambda: self.now,
            sleep=self._sleep,
            motion=self.window,
        )

    def _opacity(self, value: float) -> None:
        self.window.opacity = value

    def _show(self) -> None:
        self.window.hidden = False

    def _hide(self) -> None:
        self.window.hidden = True

    def at(self, when: Callable[[], bool], action: Callable[[], object]) -> None:
        self.hooks.append((when, action))

    def restore_when_minimized(self, after: float = 2.0) -> None:
        self.at(lambda: self.window.minimized and self.now > after, self.window.restore)

    def _sleep(self, seconds: float) -> None:
        self.now += seconds
        assert self.now < 60, "the job never ended"
        for hook in list(self.hooks):
            if hook[0]():
                self.hooks.remove(hook)
                hook[1]()

    def run(self) -> None:
        while self.jobs:
            self.jobs.pop(0)()


def test_minimize_returns_at_once() -> None:
    rig = Rig()
    rig.fade.minimize()
    assert rig.window.minimize_calls == 0
    assert len(rig.jobs) == 1


def test_it_is_invisible_and_slid_down_when_minimized() -> None:
    rig = Rig()
    rig.restore_when_minimized()
    rig.fade.minimize()
    rig.run()
    assert rig.window.opacity_at_minimize == 0.0
    assert rig.window.place_at_minimize == (HOME[0], HOME[1] + SHIFT)


def test_after_a_restore_it_rises_back_home() -> None:
    rig = Rig()
    rig.restore_when_minimized()
    rig.fade.minimize()
    rig.run()
    assert rig.window.opacity == 1.0
    assert rig.window.place == HOME


def test_it_stays_invisible_while_minimized() -> None:
    rig = Rig()
    seen: list[float] = []
    rig.at(lambda: rig.now > 5, lambda: seen.append(rig.window.opacity))
    rig.restore_when_minimized(after=6)
    rig.fade.minimize()
    rig.run()
    assert seen == [0.0]


def test_the_window_does_not_creep_down_after_many_times() -> None:
    rig = Rig()
    for _ in range(5):
        rig.restore_when_minimized(after=rig.now + 2)
        rig.fade.minimize()
        rig.run()
    assert rig.window.place == HOME


def test_a_second_request_during_the_slide_keeps_the_home_place() -> None:
    rig = Rig()
    rig.at(lambda: rig.now > 0.2, rig.fade.minimize)
    rig.restore_when_minimized()
    rig.fade.minimize()
    rig.run()
    assert rig.window.minimize_calls == 1
    assert rig.window.place == HOME


def test_close_during_the_slide_hides_without_minimizing() -> None:
    rig = Rig()
    rig.at(lambda: rig.now > 0.2, rig.fade.hide)
    rig.fade.minimize()
    rig.run()
    assert rig.window.hidden
    assert rig.window.minimize_calls == 0
    rig.fade.show()
    rig.run()
    assert rig.window.place == HOME
    assert rig.window.opacity == 1.0


def test_tray_open_restores_a_minimized_window() -> None:
    rig = Rig()
    rig.at(lambda: rig.window.minimized and rig.now > 2, rig.fade.show)
    rig.fade.minimize()
    rig.run()
    assert not rig.window.minimized
    assert rig.window.opacity == 1.0
    assert rig.window.place == HOME


def test_closed_while_minimized_then_opened() -> None:
    rig = Rig()
    rig.at(lambda: rig.window.minimized and rig.now > 2, rig.fade.hide)
    rig.fade.minimize()
    rig.run()
    assert rig.window.hidden
    rig.fade.show()
    rig.run()
    assert not rig.window.hidden and not rig.window.minimized
    assert rig.window.place == HOME
    assert rig.window.opacity == 1.0


def test_a_window_that_does_not_minimize_comes_back() -> None:
    rig = Rig(fail="ignored")
    rig.fade.minimize()
    rig.run()
    assert rig.now >= MINIMIZE_TIMEOUT
    assert rig.window.opacity == 1.0
    assert rig.window.place == HOME


def test_a_failing_minimize_call_brings_the_window_back() -> None:
    rig = Rig(fail="raises")
    rig.fade.minimize()
    rig.run()
    assert rig.window.opacity == 1.0
    assert rig.window.place == HOME


def test_minimizing_a_minimized_window_does_nothing() -> None:
    rig = Rig()
    rig.window.minimized = True
    rig.fade.minimize()
    rig.run()
    assert rig.window.minimize_calls == 0
    assert rig.window.opacity == 1.0


def test_close_stops_waiting_for_a_restore() -> None:
    rig = Rig()
    rig.at(lambda: rig.window.minimized and rig.now > 2, rig.fade.close)
    rig.fade.minimize()
    rig.run()
    assert rig.window.minimized


def test_a_plain_hide_does_not_move_the_window() -> None:
    rig = Rig()
    rig.fade.hide()
    rig.run()
    assert rig.window.moves == []
