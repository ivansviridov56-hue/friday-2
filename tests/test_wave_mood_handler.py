import pytest

from friday.wave_mood import MoodStatus
from friday.wave_mood_handler import make_wave_mood_handler


class FakeLauncher:
    def __init__(self, status: MoodStatus | Exception) -> None:
        self._status = status
        self.moods: list[str] = []

    def launch(self, mood: str) -> MoodStatus:
        self.moods.append(mood)
        if isinstance(self._status, Exception):
            raise self._status
        return self._status


PHRASE = "Включи мою спокойную волну"


def test_started_is_spoken_with_the_mood_name() -> None:
    launcher = FakeLauncher(MoodStatus.STARTED)
    reply = make_wave_mood_handler(launcher)(PHRASE)
    assert reply is not None
    assert "спокойное" in reply.text
    assert reply.spoken is True
    assert launcher.moods == ["calm"]


def test_already_set_is_spoken() -> None:
    reply = make_wave_mood_handler(FakeLauncher(MoodStatus.ALREADY_SET))(PHRASE)
    assert reply is not None
    assert "уже играет" in reply.text


def test_no_panel_tells_to_open_the_wave() -> None:
    reply = make_wave_mood_handler(FakeLauncher(MoodStatus.NO_PANEL))(PHRASE)
    assert reply is not None
    assert "Открой" in reply.text


def test_not_confirmed_has_its_own_answer() -> None:
    reply = make_wave_mood_handler(FakeLauncher(MoodStatus.NOT_CONFIRMED))(PHRASE)
    assert reply is not None
    assert "не заиграла" in reply.text


@pytest.mark.parametrize("status", list(MoodStatus))
def test_every_status_gets_a_spoken_answer(status: MoodStatus) -> None:
    reply = make_wave_mood_handler(FakeLauncher(status))(PHRASE)
    assert reply is not None
    assert reply.text
    assert reply.spoken is True


def test_launcher_crash_is_spoken_not_raised() -> None:
    launcher = FakeLauncher(RuntimeError("boom"))
    reply = make_wave_mood_handler(launcher)(PHRASE)
    assert reply is not None
    assert reply.spoken is True


def test_phrases_without_a_mood_return_none_and_do_not_launch() -> None:
    launcher = FakeLauncher(MoodStatus.STARTED)
    handler = make_wave_mood_handler(launcher)
    assert handler("Включи мою волну") is None
    assert handler("Включи свет") is None
    assert launcher.moods == []
