"""WaveLauncher calls the optional after_start hook only when My Wave really started."""

import pytest

from friday.wave_launcher import WaveLauncher, WaveStatus


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


def build(
    after_start,
    *,
    playing: bool = False,
    has_player: bool = True,
    confirms: bool = True,
    press_raises: bool = False,
) -> WaveLauncher:
    clock = Clock()
    state = {"playing": playing}

    class Player:
        def press_play(self) -> None:
            if press_raises:
                raise RuntimeError("boom")
            if confirms:
                state["playing"] = True

    return WaveLauncher(
        lambda: Player() if has_player else None,
        lambda: state["playing"],
        after_start=after_start,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )


def test_after_start_runs_once_after_a_confirmed_start() -> None:
    calls: list[str] = []
    launcher = build(lambda: calls.append("after"))
    assert launcher.launch() is WaveStatus.STARTED
    assert calls == ["after"]


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({"playing": True}, WaveStatus.ALREADY_PLAYING),
        ({"has_player": False}, WaveStatus.NO_PLAYER),
        ({"confirms": False}, WaveStatus.NOT_CONFIRMED),
        ({"press_raises": True}, WaveStatus.ERROR),
    ],
)
def test_after_start_is_skipped_unless_started(options, expected) -> None:
    calls: list[str] = []
    launcher = build(lambda: calls.append("after"), **options)
    assert launcher.launch() is expected
    assert calls == []


def test_a_failing_after_start_does_not_change_the_result() -> None:
    def broken() -> None:
        raise RuntimeError("boom")

    launcher = build(broken)
    assert launcher.launch() is WaveStatus.STARTED
