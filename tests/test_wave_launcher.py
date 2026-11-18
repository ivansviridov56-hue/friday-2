from friday.wave_launcher import WaveLauncher, WaveStatus


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


class FakePlayer:
    def __init__(self, fail: bool = False) -> None:
        self.presses = 0
        self._fail = fail

    def press_play(self) -> None:
        if self._fail:
            raise RuntimeError("boom")
        self.presses += 1


def make(find_player, is_playing) -> WaveLauncher:
    clock = Clock()
    return WaveLauncher(
        find_player, is_playing, sleep=clock.sleep, monotonic=clock.monotonic
    )


def test_started_when_playback_is_confirmed() -> None:
    player = FakePlayer()
    launcher = make(lambda: player, lambda: player.presses > 0)
    assert launcher.launch() is WaveStatus.STARTED
    assert player.presses == 1


def test_already_playing_presses_nothing() -> None:
    player = FakePlayer()
    calls = []
    launcher = make(lambda: calls.append(1) or player, lambda: True)
    assert launcher.launch() is WaveStatus.ALREADY_PLAYING
    assert player.presses == 0
    assert calls == []


def test_no_player_when_never_found() -> None:
    launcher = make(lambda: None, lambda: False)
    assert launcher.launch() is WaveStatus.NO_PLAYER


def test_lookup_error_counts_as_not_found() -> None:
    def broken():
        raise RuntimeError("boom")

    launcher = make(broken, lambda: False)
    assert launcher.launch() is WaveStatus.NO_PLAYER


def test_player_that_appears_later_is_used() -> None:
    player = FakePlayer()
    found = iter([None, None, player])
    launcher = make(lambda: next(found), lambda: player.presses > 0)
    assert launcher.launch() is WaveStatus.STARTED
    assert player.presses == 1


def test_not_confirmed_when_session_stays_silent() -> None:
    player = FakePlayer()
    launcher = make(lambda: player, lambda: False)
    assert launcher.launch() is WaveStatus.NOT_CONFIRMED
    assert player.presses == 1


def test_error_when_press_fails() -> None:
    launcher = make(lambda: FakePlayer(fail=True), lambda: False)
    assert launcher.launch() is WaveStatus.ERROR


def test_playback_check_error_is_treated_as_not_playing() -> None:
    player = FakePlayer()
    state = {"first": True}

    def flaky() -> bool:
        if state["first"]:
            state["first"] = False
            raise RuntimeError("boom")
        return player.presses > 0

    launcher = make(lambda: player, flaky)
    assert launcher.launch() is WaveStatus.STARTED
