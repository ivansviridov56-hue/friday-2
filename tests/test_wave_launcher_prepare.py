"""WaveLauncher calls the optional prepare hook before looking for the player."""

from friday.wave_launcher import WaveLauncher, WaveStatus


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


def build(prepare, events: list[str], playing: bool = False) -> WaveLauncher:
    clock = Clock()
    state = {"playing": playing}

    class Player:
        def press_play(self) -> None:
            events.append("press")
            state["playing"] = True

    def find_player():
        events.append("find")
        return Player()

    return WaveLauncher(
        find_player,
        lambda: state["playing"],
        prepare=prepare,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )


def test_prepare_runs_before_the_player_lookup() -> None:
    events: list[str] = []
    launcher = build(lambda: events.append("prepare"), events)
    assert launcher.launch() is WaveStatus.STARTED
    assert events == ["prepare", "find", "press"]


def test_prepare_is_skipped_when_something_already_plays() -> None:
    events: list[str] = []
    launcher = build(lambda: events.append("prepare"), events, playing=True)
    assert launcher.launch() is WaveStatus.ALREADY_PLAYING
    assert events == []


def test_a_failing_prepare_does_not_stop_the_launch() -> None:
    events: list[str] = []

    def broken() -> None:
        raise RuntimeError("boom")

    launcher = build(broken, events)
    assert launcher.launch() is WaveStatus.STARTED
    assert events == ["find", "press"]
