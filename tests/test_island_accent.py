import pytest

from friday.island_logic import color_for, is_hex_color

ACCENT = "#4CC2FF"


@pytest.mark.parametrize("state", ["loading", "idle"])
def test_win11_calm_states_follow_the_accent(state: str) -> None:
    assert color_for(state, "win11", ACCENT) == "#4cc2ff"


@pytest.mark.parametrize("state", ["listening", "thinking", "speaking", "error"])
def test_win11_active_states_keep_their_colours(state: str) -> None:
    assert color_for(state, "win11", ACCENT) == color_for(state, "win11")


@pytest.mark.parametrize("theme", ["classic", "windows", "black"])
def test_other_themes_ignore_the_accent(theme: str) -> None:
    assert color_for("idle", theme, ACCENT) == color_for("idle", theme)


def test_without_accent_win11_idle_is_the_default_blue() -> None:
    assert color_for("idle", "win11") == "#3aa6d8"
    assert color_for("idle", "win11", None) == "#3aa6d8"


@pytest.mark.parametrize("bad", ["", "red", "#12345", "#1234567", "4cc2ff", "#gggggg"])
def test_bad_accent_is_ignored(bad: str) -> None:
    assert color_for("idle", "win11", bad) == "#3aa6d8"


@pytest.mark.parametrize("value", ["#000000", "#4cc2ff", "#ABCDEF"])
def test_is_hex_color_accepts_rgb(value: str) -> None:
    assert is_hex_color(value)


@pytest.mark.parametrize("value", [None, "", "#fff", "#12345g", " #4cc2ff"])
def test_is_hex_color_rejects_the_rest(value: str | None) -> None:
    assert not is_hex_color(value)
