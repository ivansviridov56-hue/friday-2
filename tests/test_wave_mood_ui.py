from types import SimpleNamespace

import pytest

from friday.wave_mood_ui import (
    CLOSE_NAME,
    UiaWaveMoodUi,
    clean,
    mood_from_reset_name,
)


class FakeButton:
    def __init__(self, name, width=100, height=40, toggle=0, on_invoke=None):
        self.element_info = SimpleNamespace(
            name=name,
            rectangle=SimpleNamespace(width=lambda: width, height=lambda: height),
        )
        self.toggle = toggle
        self.invoked = 0
        self._on_invoke = on_invoke

    def invoke(self):
        self.invoked += 1
        if self._on_invoke:
            self._on_invoke()

    def get_toggle_state(self):
        return self.toggle


class FakeWindow:
    def __init__(self, buttons):
        self.buttons = list(buttons)

    def descendants(self, control_type):
        assert control_type == "Button"
        return list(self.buttons)


def make(window):
    return UiaWaveMoodUi(window, settle=0, sleep=lambda seconds: None)


def test_clean_normalizes_spaces_and_case() -> None:
    assert clean("  Закрыть\xa0меню настроек ") == CLOSE_NAME


@pytest.mark.parametrize(
    ("name", "mood"),
    [
        ("Сбросить Весёлое и включить Мою волну", "fun"),
        ("Сбросить\xa0Спокойное и включить Мою волну", "calm"),
        ("Сбросить Что-то и включить Мою волну", None),
        ("Сбросить  и включить Мою волну", None),
        ("Настроить Мою волну", None),
        ("", None),
        (None, None),
    ],
)
def test_mood_from_reset_name(name, mood) -> None:
    assert mood_from_reset_name(name) is mood


def test_current_mood_reads_the_visible_plate() -> None:
    window = FakeWindow([FakeButton("Сбросить Весёлое и включить Мою волну")])
    assert make(window).current_mood() == "fun"


def test_current_mood_ignores_hidden_copies() -> None:
    hidden = FakeButton("Сбросить Спокойное и включить Мою волну", width=0, height=0)
    assert make(FakeWindow([hidden])).current_mood() is None


def test_current_mood_none_without_plate() -> None:
    assert make(FakeWindow([FakeButton("Настроить Мою волну")])).current_mood() is None


def test_reset_presses_only_the_visible_plate() -> None:
    hidden = FakeButton("Сбросить Весёлое и включить Мою волну", width=0, height=0)
    visible = FakeButton("Сбросить Весёлое и включить Мою волну")
    make(FakeWindow([hidden, visible])).reset_mood()
    assert (hidden.invoked, visible.invoked) == (0, 1)


def test_reset_without_plate_raises() -> None:
    with pytest.raises(RuntimeError):
        make(FakeWindow([])).reset_mood()


def test_panel_open_follows_the_close_button() -> None:
    assert make(FakeWindow([FakeButton("Закрыть меню настроек")])).panel_open()
    assert not make(FakeWindow([FakeButton("Настроить Мою волну")])).panel_open()


def test_open_panel_presses_a_hidden_settings_button() -> None:
    window = FakeWindow([])
    opener = FakeButton(
        "Настроить Мою волну",
        width=0,
        height=0,
        on_invoke=lambda: window.buttons.append(FakeButton("Закрыть меню настроек")),
    )
    window.buttons.append(opener)
    assert make(window).open_panel() is True
    assert opener.invoked == 1


def test_open_panel_does_nothing_when_already_open() -> None:
    opener = FakeButton("Настроить Мою волну")
    window = FakeWindow([FakeButton("Закрыть меню настроек"), opener])
    assert make(window).open_panel() is True
    assert opener.invoked == 0


def test_open_panel_false_without_settings_button() -> None:
    assert make(FakeWindow([])).open_panel() is False


def test_open_panel_false_when_the_panel_never_opens() -> None:
    opener = FakeButton("Настроить Мою волну")
    assert make(FakeWindow([opener])).open_panel() is False
    assert opener.invoked == 1


def test_press_mood_presses_the_right_button() -> None:
    calm = FakeButton("Спокойное")
    fun = FakeButton("Весёлое")
    make(FakeWindow([fun, calm])).press_mood("calm")
    assert (calm.invoked, fun.invoked) == (1, 0)


def test_press_mood_does_not_unselect_a_selected_mood() -> None:
    calm = FakeButton("Спокойное", toggle=1)
    make(FakeWindow([calm])).press_mood("calm")
    assert calm.invoked == 0


@pytest.mark.parametrize("count", [0, 2])
def test_press_mood_needs_exactly_one_button(count) -> None:
    window = FakeWindow([FakeButton("Спокойное") for _ in range(count)])
    with pytest.raises(RuntimeError):
        make(window).press_mood("calm")


def test_mood_selected_reads_the_toggle_state() -> None:
    assert make(FakeWindow([FakeButton("Спокойное", toggle=1)])).mood_selected("calm")
    assert not make(FakeWindow([FakeButton("Спокойное", toggle=0)])).mood_selected(
        "calm"
    )
    assert not make(FakeWindow([])).mood_selected("calm")


def test_close_panel_presses_the_close_button() -> None:
    close = FakeButton("Закрыть меню настроек")
    make(FakeWindow([close])).close_panel()
    assert close.invoked == 1


def test_close_panel_without_button_is_quiet() -> None:
    make(FakeWindow([])).close_panel()
