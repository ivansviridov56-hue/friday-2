import pytest

from friday.wave_mood import (
    MOOD_NAMES,
    MoodStatus,
    WaveMoodLauncher,
    mood_from_name,
)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def monotonic(self) -> float:
        return self.now


class FakeUi:
    def __init__(
        self,
        current=None,
        *,
        playing=False,
        button_delay=0,
        panel_appears=True,
        press_selects=True,
        press_plays=True,
        reset_clears=True,
        press_raises=False,
    ) -> None:
        self.current = current
        self.playing = playing
        self.button_delay = button_delay
        self.panel_appears = panel_appears
        self.press_selects = press_selects
        self.press_plays = press_plays
        self.reset_clears = reset_clears
        self.press_raises = press_raises
        self.panel = False
        self.selected = None
        self.calls: list[str] = []

    def current_mood(self):
        return self.current

    def reset_mood(self) -> None:
        self.calls.append("reset")
        if self.reset_clears:
            self.current = None

    def open_panel(self) -> bool:
        self.calls.append("open")
        if self.button_delay > 0:
            self.button_delay -= 1
            return False
        self.panel = self.panel_appears
        return True

    def panel_open(self) -> bool:
        return self.panel

    def press_mood(self, mood: str) -> None:
        if self.press_raises:
            raise RuntimeError("boom")
        self.calls.append(f"press:{mood}")
        if self.press_selects:
            self.selected = mood
            self.current = mood
        if self.press_plays:
            self.playing = True

    def mood_selected(self, mood: str) -> bool:
        return self.selected == mood

    def close_panel(self) -> None:
        self.calls.append("close")
        self.panel = False


def make(ui, *, found=True, **kwargs) -> WaveMoodLauncher:
    clock = Clock()
    return WaveMoodLauncher(
        lambda: ui if found else None,
        lambda: ui.playing,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
        **kwargs,
    )


def test_nothing_selected_opens_panel_presses_and_closes() -> None:
    ui = FakeUi()
    assert make(ui).launch("calm") is MoodStatus.STARTED
    assert ui.calls == ["open", "press:calm", "close"]


def test_same_mood_already_playing_presses_nothing() -> None:
    ui = FakeUi(current="calm", playing=True)
    assert make(ui).launch("calm") is MoodStatus.ALREADY_SET
    assert ui.calls == []


def test_other_mood_is_reset_first() -> None:
    ui = FakeUi(current="fun", playing=True)
    assert make(ui).launch("calm") is MoodStatus.STARTED
    assert ui.calls == ["reset", "open", "press:calm", "close"]


def test_same_mood_on_pause_is_reset_and_chosen_again() -> None:
    ui = FakeUi(current="calm", playing=False)
    assert make(ui).launch("calm") is MoodStatus.STARTED
    assert ui.calls == ["reset", "open", "press:calm", "close"]


def test_no_window() -> None:
    ui = FakeUi()
    assert make(ui, found=False).launch("calm") is MoodStatus.NO_WINDOW
    assert ui.calls == []


@pytest.mark.parametrize(
    "ui",
    [FakeUi(button_delay=10_000), FakeUi(panel_appears=False)],
    ids=["no-open-button", "panel-does-not-appear"],
)
def test_panel_that_cannot_be_opened(ui: FakeUi) -> None:
    assert make(ui).launch("calm") is MoodStatus.NO_PANEL
    assert not any(call.startswith("press") for call in ui.calls)


def test_open_button_that_appears_late_is_waited_for() -> None:
    ui = FakeUi(button_delay=3)
    assert make(ui).launch("calm") is MoodStatus.STARTED
    assert ui.calls.count("press:calm") == 1


def test_reset_that_does_not_clear_the_mood_stops_the_chain() -> None:
    ui = FakeUi(current="fun", playing=True, reset_clears=False)
    assert make(ui).launch("calm") is MoodStatus.NOT_CONFIRMED
    assert not any(call.startswith("press") for call in ui.calls)


def test_press_that_does_not_select_the_mood() -> None:
    ui = FakeUi(press_selects=False)
    assert make(ui).launch("calm") is MoodStatus.NOT_CONFIRMED


def test_mood_selected_but_nothing_plays() -> None:
    ui = FakeUi(press_plays=False)
    assert make(ui).launch("calm") is MoodStatus.NOT_CONFIRMED


def test_ui_error_while_pressing() -> None:
    ui = FakeUi(press_raises=True)
    assert make(ui).launch("calm") is MoodStatus.ERROR


@pytest.mark.parametrize("mood", ["rock", ""])
def test_unknown_mood_touches_nothing(mood: str) -> None:
    ui = FakeUi()
    assert make(ui).launch(mood) is MoodStatus.ERROR
    assert ui.calls == []


def test_failing_close_does_not_spoil_the_result() -> None:
    ui = FakeUi()

    def boom() -> None:
        raise RuntimeError("boom")

    ui.close_panel = boom  # type: ignore[method-assign]
    assert make(ui).launch("calm") is MoodStatus.STARTED


def test_window_is_restored_before_and_minimized_back_after() -> None:
    events: list[str] = []
    ui = FakeUi()
    launcher = make(
        ui,
        prepare=lambda: events.append("prepare"),
        after_start=lambda: events.append("after"),
    )
    assert launcher.launch("calm") is MoodStatus.STARTED
    assert events == ["prepare", "after"]


def test_window_is_minimized_back_when_the_mood_was_already_set() -> None:
    events: list[str] = []
    ui = FakeUi(current="calm", playing=True)
    launcher = make(
        ui,
        prepare=lambda: events.append("prepare"),
        after_start=lambda: events.append("after"),
    )
    assert launcher.launch("calm") is MoodStatus.ALREADY_SET
    assert events == ["prepare", "after"]


def test_cold_start_opens_the_wave_link_and_waits_for_the_window() -> None:
    ui = FakeUi()
    opened: list[int] = []
    clock = Clock()
    launcher = WaveMoodLauncher(
        lambda: ui if opened else None,
        lambda: ui.playing,
        is_running=lambda: False,
        open_wave=lambda: opened.append(1),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert launcher.launch("calm") is MoodStatus.STARTED
    assert opened == [1]


def test_running_app_does_not_get_the_wave_link() -> None:
    ui = FakeUi()
    opened: list[int] = []
    launcher = make(ui, is_running=lambda: True, open_wave=lambda: opened.append(1))
    assert launcher.launch("calm") is MoodStatus.STARTED
    assert opened == []


def test_mood_names_cover_the_four_moods() -> None:
    assert MOOD_NAMES == {
        "active": "Бодрое",
        "fun": "Весёлое",
        "calm": "Спокойное",
        "sad": "Грустное",
    }


@pytest.mark.parametrize(
    ("name", "mood"),
    [
        ("Бодрое", "active"),
        ("Весёлое", "fun"),
        ("весёлое", "fun"),
        ("Веселое", "fun"),
        ("Спокойное\xa0", "calm"),
        ("Грустное", "sad"),
        ("Что-то другое", None),
        ("", None),
    ],
)
def test_mood_from_name(name: str, mood: str | None) -> None:
    assert mood_from_name(name) == mood
