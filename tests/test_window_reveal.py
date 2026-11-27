"""The cloaked window is revealed once: when it is ready, on request or by timeout."""

from __future__ import annotations

from collections.abc import Callable

from friday.window_reveal import SETTLE_DELAY, TIMEOUT, WindowReveal


class FakeTimer:
    def __init__(self, delay: float, action: Callable[[], object]) -> None:
        self.delay = delay
        self.action = action
        self.daemon = False
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        assert self.started and not self.cancelled
        self.action()


class Rig:
    def __init__(self, results: list[bool] | None = None) -> None:
        self.calls = 0
        self.timers: list[FakeTimer] = []
        self._results = results or []
        self.reveal = WindowReveal(self._uncloak, self._timer)

    def _uncloak(self) -> bool:
        self.calls += 1
        return self._results.pop(0) if self._results else True

    def _timer(self, delay: float, action: Callable[[], object]) -> FakeTimer:
        timer = FakeTimer(delay, action)
        self.timers.append(timer)
        return timer


def test_arm_starts_only_the_safety_timer() -> None:
    rig = Rig()
    rig.reveal.arm(True)
    assert [t.delay for t in rig.timers] == [TIMEOUT]
    assert rig.timers[0].started and rig.timers[0].daemon
    assert rig.calls == 0


def test_ready_reveals_after_the_settle_delay() -> None:
    rig = Rig()
    rig.reveal.arm(True)
    rig.reveal.ready()
    assert rig.calls == 0
    assert rig.timers[1].delay == SETTLE_DELAY
    rig.timers[1].fire()
    assert rig.calls == 1
    assert all(t.cancelled for t in rig.timers)


def test_second_ready_starts_no_new_timer() -> None:
    rig = Rig()
    rig.reveal.arm(True)
    rig.reveal.ready()
    rig.reveal.ready()
    assert len(rig.timers) == 2


def test_safety_timer_reveals_when_ready_never_comes() -> None:
    rig = Rig()
    rig.reveal.arm(True)
    rig.timers[0].fire()
    assert rig.calls == 1


def test_reveal_on_request_works_only_once() -> None:
    rig = Rig()
    rig.reveal.arm(True)
    assert rig.reveal.reveal() is True
    assert rig.reveal.reveal() is False
    rig.reveal.ready()
    assert rig.calls == 1
    assert len(rig.timers) == 1


def test_failed_cloak_needs_no_reveal() -> None:
    rig = Rig()
    rig.reveal.arm(False)
    rig.reveal.ready()
    assert rig.reveal.reveal() is False
    assert rig.calls == 0
    assert rig.timers == []


def test_failed_uncloak_can_be_retried() -> None:
    rig = Rig(results=[False, True])
    rig.reveal.arm(True)
    assert rig.reveal.reveal() is False
    assert rig.reveal.reveal() is True
    assert rig.calls == 2


def test_raising_uncloak_is_caught_and_can_be_retried() -> None:
    attempts: list[int] = []

    def uncloak() -> bool:
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("boom")
        return True

    reveal = WindowReveal(uncloak, FakeTimer)
    reveal.arm(True)
    assert reveal.reveal() is False
    assert reveal.reveal() is True


def test_ready_before_arm_is_remembered() -> None:
    rig = Rig()
    rig.reveal.ready()
    rig.reveal.arm(True)
    assert [t.delay for t in rig.timers] == [TIMEOUT, SETTLE_DELAY]


def test_close_cancels_timers_and_blocks_reveal() -> None:
    rig = Rig()
    rig.reveal.arm(True)
    rig.reveal.ready()
    rig.reveal.close()
    assert all(t.cancelled for t in rig.timers)
    assert rig.reveal.reveal() is False
    assert rig.calls == 0


def test_delays_are_sensible() -> None:
    # The page fades in for 0.5 s; that must finish while the window is still cloaked.
    assert SETTLE_DELAY >= 0.5
    assert SETTLE_DELAY < TIMEOUT <= 10
