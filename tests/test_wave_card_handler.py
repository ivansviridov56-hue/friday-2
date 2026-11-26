import pytest

from friday.wave_card_handler import make_wave_card_handler
from friday.wave_card_launcher import CardResult, CardStatus

PHRASE = "Включи волну русский поп-рок"


class FakeLauncher:
    def __init__(self, result: CardResult | Exception) -> None:
        self._result = result
        self.queries: list[str] = []

    def launch(self, query: str) -> CardResult:
        self.queries.append(query)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def test_started_is_spoken_with_the_card_title() -> None:
    launcher = FakeLauncher(CardResult(CardStatus.STARTED, "Русский поп-рок"))
    reply = make_wave_card_handler(launcher)(PHRASE)
    assert reply is not None
    assert reply.text == "Включаю волну: Русский поп-рок."
    assert reply.spoken is True
    assert launcher.queries == ["русский поп рок"]


def test_no_match_has_its_own_answer() -> None:
    launcher = FakeLauncher(CardResult(CardStatus.NO_MATCH))
    reply = make_wave_card_handler(launcher)(PHRASE)
    assert reply is not None
    assert "Не нашла" in reply.text


@pytest.mark.parametrize("status", list(CardStatus))
def test_every_status_gets_a_spoken_answer(status: CardStatus) -> None:
    launcher = FakeLauncher(CardResult(status, "Любимое"))
    reply = make_wave_card_handler(launcher)(PHRASE)
    assert reply is not None
    assert reply.text
    assert reply.spoken is True


def test_launcher_crash_is_spoken_not_raised() -> None:
    reply = make_wave_card_handler(FakeLauncher(RuntimeError("boom")))(PHRASE)
    assert reply is not None
    assert reply.spoken is True


def test_phrases_without_a_card_title_return_none_and_do_not_launch() -> None:
    launcher = FakeLauncher(CardResult(CardStatus.STARTED, "Любимое"))
    handler = make_wave_card_handler(launcher)
    assert handler("Включи мою волну") is None
    assert handler("Включи свет") is None
    assert launcher.queries == []


@pytest.mark.parametrize(
    "status", [CardStatus.NO_WINDOW, CardStatus.NO_CARDS, CardStatus.NO_MATCH]
)
def test_plain_wave_phrase_falls_through_when_nothing_was_pressed(status) -> None:
    launcher = FakeLauncher(CardResult(status))
    assert make_wave_card_handler(launcher)("Включи мою волну снова") is None
    assert launcher.queries == ["снова"]


@pytest.mark.parametrize(
    "status", [CardStatus.STARTED, CardStatus.NOT_CONFIRMED, CardStatus.ERROR]
)
def test_plain_wave_phrase_is_answered_once_a_card_was_chosen(status) -> None:
    launcher = FakeLauncher(CardResult(status, "Любимое"))
    reply = make_wave_card_handler(launcher)("Включи мою волну любимое")
    assert reply is not None
    assert reply.spoken is True
