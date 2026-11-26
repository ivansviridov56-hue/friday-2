from types import SimpleNamespace

from friday.wave_card_launcher import CardStatus, WaveCardLauncher
from friday.wave_card_ui import UiaWaveCardUi

POP = "Моя волна по жанру Это поп!"


class FakeControl:
    def __init__(self, name, width=419, height=101, broken=False, on_invoke=None):
        self.width = width
        self.height = height
        self.broken = broken
        self.invoked = 0
        self.on_invoke = on_invoke
        self.element_info = SimpleNamespace(
            name=name,
            rectangle=SimpleNamespace(
                width=lambda: self.width, height=lambda: self.height
            ),
        )

    def invoke(self):
        self.invoked += 1
        if self.broken:
            raise RuntimeError("gone")
        if self.on_invoke:
            self.on_invoke()


def hidden(name):
    return FakeControl(name, width=0, height=0)


class FakeWindow:
    def __init__(self, groups=(), buttons=()):
        self.controls = {"Group": list(groups), "Button": list(buttons)}

    def descendants(self, control_type):
        return list(self.controls[control_type])


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


def test_card_names_come_from_groups_and_buttons() -> None:
    window = FakeWindow(
        groups=[FakeControl(POP)], buttons=[FakeControl("Моя волна Энергичный поп")]
    )
    assert UiaWaveCardUi(window).card_names() == [POP, "Моя волна Энергичный поп"]


def test_card_names_skip_everything_that_is_not_a_wave_card() -> None:
    names = ["Моя волна", "Настроить Мою волну", "Сингл Претендент", "", None]
    window = FakeWindow(groups=[FakeControl(name) for name in names])
    assert UiaWaveCardUi(window).card_names() == []


def test_a_name_with_a_non_breaking_space_is_found() -> None:
    card = FakeControl("Моя волна по жанру Это\xa0поп!")
    ui = UiaWaveCardUi(FakeWindow(groups=[card]))
    assert ui.card_visible(POP)
    assert ui.press_card(POP)
    assert card.invoked == 1


def test_card_is_visible_if_any_copy_has_a_size() -> None:
    window = FakeWindow(groups=[hidden(POP), FakeControl(POP)])
    assert UiaWaveCardUi(window).card_visible(POP)


def test_card_with_only_hidden_copies_is_not_visible() -> None:
    window = FakeWindow(groups=[hidden(POP), hidden(POP)])
    assert not UiaWaveCardUi(window).card_visible(POP)


def test_press_takes_the_visible_copy() -> None:
    first, second = hidden(POP), FakeControl(POP)
    assert UiaWaveCardUi(FakeWindow(groups=[first, second])).press_card(POP)
    assert (first.invoked, second.invoked) == (0, 1)


def test_press_invokes_one_hidden_copy_when_none_is_visible() -> None:
    first, second = hidden(POP), hidden(POP)
    assert UiaWaveCardUi(FakeWindow(groups=[first, second])).press_card(POP)
    assert (first.invoked, second.invoked) == (1, 0)


def test_failed_visible_copy_never_falls_back_to_a_hidden_one() -> None:
    spare, visible = hidden(POP), FakeControl(POP, broken=True)
    assert not UiaWaveCardUi(FakeWindow(groups=[spare, visible])).press_card(POP)
    assert spare.invoked == 0


def test_press_of_a_missing_card_is_false() -> None:
    assert not UiaWaveCardUi(FakeWindow()).press_card(POP)


def test_launcher_scrolls_to_a_hidden_card_and_presses_it_again() -> None:
    card = hidden(POP)

    def scroll_into_view() -> None:
        card.width, card.height = 419, 101

    card.on_invoke = scroll_into_view
    ui = UiaWaveCardUi(FakeWindow(groups=[card]))
    clock = FakeClock()
    launcher = WaveCardLauncher(
        lambda: ui, lambda: True, sleep=clock.sleep, monotonic=clock.monotonic
    )
    assert launcher.launch("это поп").status is CardStatus.STARTED
    assert card.invoked == 2
