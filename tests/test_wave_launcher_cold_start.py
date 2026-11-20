"""Tests for starting My Wave when Yandex Music is closed."""

from __future__ import annotations

from friday.wave_launcher import WaveLauncher, WaveStatus


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class FakePlayer:
    def __init__(self, on_press) -> None:
        self._on_press = on_press

    def press_play(self) -> None:
        self._on_press()


def _launcher(clock, *, running, open_wave, player_at, playing_at_start=False):
    pressed: list[int] = []

    def find_player():
        if clock.now >= player_at:
            return FakePlayer(lambda: pressed.append(1))
        return None

    launcher = WaveLauncher(
        find_player,
        lambda: playing_at_start or bool(pressed),
        is_running=running,
        open_wave=open_wave,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
        player_timeout=5.0,
        cold_start_timeout=20.0,
        confirm_timeout=5.0,
        poll_interval=0.3,
    )
    return launcher, pressed


def test_closed_app_opens_the_link_and_waits_for_the_player() -> None:
    clock = Clock()
    opened: list[int] = []
    launcher, pressed = _launcher(
        clock, running=lambda: False, open_wave=lambda: opened.append(1), player_at=12.0
    )
    assert launcher.launch() is WaveStatus.STARTED
    assert opened == [1]
    assert pressed == [1]


def test_running_app_does_not_open_the_link() -> None:
    clock = Clock()
    opened: list[int] = []
    launcher, _ = _launcher(
        clock, running=lambda: True, open_wave=lambda: opened.append(1), player_at=0.0
    )
    assert launcher.launch() is WaveStatus.STARTED
    assert opened == []


def test_running_app_keeps_the_short_timeout() -> None:
    clock = Clock()
    launcher, pressed = _launcher(
        clock, running=lambda: True, open_wave=lambda: None, player_at=15.0
    )
    assert launcher.launch() is WaveStatus.NO_PLAYER
    assert pressed == []
    assert clock.now < 10.0


def test_closed_app_gives_up_after_the_cold_start_timeout() -> None:
    clock = Clock()
    opened: list[int] = []
    launcher, pressed = _launcher(
        clock,
        running=lambda: False,
        open_wave=lambda: opened.append(1),
        player_at=1000.0,
    )
    assert launcher.launch() is WaveStatus.NO_PLAYER
    assert opened == [1]
    assert pressed == []
    assert clock.now >= 20.0


def test_already_playing_does_not_open_the_link() -> None:
    clock = Clock()
    opened: list[int] = []
    launcher, pressed = _launcher(
        clock,
        running=lambda: False,
        open_wave=lambda: opened.append(1),
        player_at=0.0,
        playing_at_start=True,
    )
    assert launcher.launch() is WaveStatus.ALREADY_PLAYING
    assert opened == []
    assert pressed == []


def test_failing_open_falls_back_to_the_short_timeout() -> None:
    clock = Clock()

    def boom() -> None:
        raise OSError("no handler")

    launcher, _ = _launcher(
        clock, running=lambda: False, open_wave=boom, player_at=1000.0
    )
    assert launcher.launch() is WaveStatus.NO_PLAYER
    assert clock.now < 10.0


def test_failing_running_check_does_not_open_the_link() -> None:
    clock = Clock()
    opened: list[int] = []

    def boom() -> bool:
        raise RuntimeError("tasklist failed")

    launcher, _ = _launcher(
        clock, running=boom, open_wave=lambda: opened.append(1), player_at=1000.0
    )
    assert launcher.launch() is WaveStatus.NO_PLAYER
    assert opened == []
    assert clock.now < 10.0
