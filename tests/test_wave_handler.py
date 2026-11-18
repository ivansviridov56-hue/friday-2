import pytest

from friday.wave_handler import make_wave_handler
from friday.wave_launcher import WaveStatus


class FakeLauncher:
    def __init__(self, status: WaveStatus | Exception) -> None:
        self._status = status
        self.calls = 0

    def launch(self) -> WaveStatus:
        self.calls += 1
        if isinstance(self._status, Exception):
            raise self._status
        return self._status


def test_started_is_spoken() -> None:
    reply = make_wave_handler(FakeLauncher(WaveStatus.STARTED))("Включи мою волну")
    assert reply is not None
    assert reply.text == "Включаю Мою волну"
    assert reply.spoken is True


def test_already_playing_is_spoken() -> None:
    reply = make_wave_handler(FakeLauncher(WaveStatus.ALREADY_PLAYING))("Моя волна")
    assert reply is not None
    assert "уже играет" in reply.text
    assert reply.spoken is True


def test_no_player_tells_to_open_the_wave() -> None:
    reply = make_wave_handler(FakeLauncher(WaveStatus.NO_PLAYER))("Включи мою волну")
    assert reply is not None
    assert "Открой" in reply.text
    assert reply.spoken is True


@pytest.mark.parametrize("status", list(WaveStatus))
def test_every_status_gets_a_spoken_answer(status: WaveStatus) -> None:
    reply = make_wave_handler(FakeLauncher(status))("Включи мою волну")
    assert reply is not None
    assert reply.text
    assert reply.spoken is True


def test_launcher_crash_is_spoken_not_raised() -> None:
    launcher = FakeLauncher(RuntimeError("boom"))
    reply = make_wave_handler(launcher)("Включи мою волну")
    assert reply is not None
    assert reply.spoken is True


def test_other_phrases_return_none_and_do_not_launch() -> None:
    launcher = FakeLauncher(WaveStatus.STARTED)
    handler = make_wave_handler(launcher)
    assert handler("Включи свет") is None
    assert handler("Что такое моя волна") is None
    assert launcher.calls == 0


def test_not_confirmed_has_its_own_answer() -> None:
    reply = make_wave_handler(FakeLauncher(WaveStatus.NOT_CONFIRMED))("Моя волна")
    assert reply is not None
    assert "не заиграла" in reply.text
    assert reply.spoken is True
