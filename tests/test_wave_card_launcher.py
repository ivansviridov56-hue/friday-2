from friday.wave_card_launcher import CardStatus, WaveCardLauncher

NAMES = [
    "Моя волна по жанру Это поп!",
    "Сингл Претендент На Убийство",
    "Моя волна по жанру Украинский рок",
]


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


class FakeUi:
    def __init__(self, names=NAMES, hidden_presses=0, press_ok=True) -> None:
        self.names = names
        self.hidden_left = hidden_presses  # presses until the card is in view
        self.press_ok = press_ok
        self.presses: list[str] = []

    def card_names(self) -> list[str]:
        return list(self.names)

    def card_visible(self, name: str) -> bool:
        return self.hidden_left <= 0

    def press_card(self, name: str) -> bool:
        self.presses.append(name)
        if self.hidden_left > 0:
            self.hidden_left -= 1
        return self.press_ok


def make(ui, playing=True, **kwargs):
    clock = FakeClock()
    launcher = WaveCardLauncher(
        lambda: ui,
        lambda: playing,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
        **kwargs,
    )
    return launcher


def test_started_when_the_card_is_visible_and_music_plays():
    ui = FakeUi()
    result = make(ui).launch("украинский рок")
    assert result.status is CardStatus.STARTED
    assert result.title == "Украинский рок"
    assert ui.presses == ["Моя волна по жанру Украинский рок"]


def test_hidden_card_is_scrolled_to_then_pressed_again():
    ui = FakeUi(hidden_presses=1)
    result = make(ui).launch("это поп")
    assert result.status is CardStatus.STARTED
    assert ui.presses == ["Моя волна по жанру Это поп!"] * 2


def test_hidden_card_that_never_shows_is_not_confirmed():
    ui = FakeUi(hidden_presses=99)
    result = make(ui).launch("это поп")
    assert result.status is CardStatus.NOT_CONFIRMED
    assert len(ui.presses) == 1


def test_no_window():
    clock = FakeClock()
    launcher = WaveCardLauncher(
        lambda: None,
        lambda: True,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert launcher.launch("поп").status is CardStatus.NO_WINDOW
    assert clock.now >= 5.0  # it waited for the window before giving up


def test_no_cards_on_the_page():
    assert make(FakeUi(names=[])).launch("поп").status is CardStatus.NO_CARDS


def test_no_match_presses_nothing():
    ui = FakeUi()
    result = make(ui).launch("джаз")
    assert result.status is CardStatus.NO_MATCH
    assert ui.presses == []


def test_press_that_fails_is_an_error_with_the_title():
    result = make(FakeUi(press_ok=False)).launch("украинский рок")
    assert result.status is CardStatus.ERROR
    assert result.title == "Украинский рок"


def test_music_that_does_not_play_is_not_confirmed():
    result = make(FakeUi(), playing=False).launch("украинский рок")
    assert result.status is CardStatus.NOT_CONFIRMED


def test_exception_in_the_ui_is_an_error_and_after_start_still_runs():
    class Broken(FakeUi):
        def card_names(self):
            raise RuntimeError("window vanished")

    calls: list[str] = []
    launcher = make(Broken(), after_start=lambda: calls.append("after"))
    assert launcher.launch("поп").status is CardStatus.ERROR
    assert calls == ["after"]


def test_prepare_and_after_start_run_around_a_successful_launch():
    calls: list[str] = []
    launcher = make(
        FakeUi(),
        prepare=lambda: calls.append("prepare"),
        after_start=lambda: calls.append("after"),
    )
    assert launcher.launch("украинский рок").status is CardStatus.STARTED
    assert calls == ["prepare", "after"]
