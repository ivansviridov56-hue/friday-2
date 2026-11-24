import re

import pytest

from friday.island_logic import (
    DEFAULT_COLOR,
    STATE_COLORS,
    color_for,
    island_position,
    BODY_COLORS,
    STATE_COLORS_BY_THEME,
    TEXT_COLORS,
    body_for,
    clip_text,
)

THEMES = ["classic", "windows", "black", "win11"]


@pytest.mark.parametrize("theme", THEMES)
def test_every_theme_has_every_state(theme):
    assert set(STATE_COLORS_BY_THEME[theme]) == set(STATE_COLORS)


@pytest.mark.parametrize("theme", THEMES)
def test_every_theme_has_body_and_text_colours(theme):
    assert re.fullmatch(r"#[0-9a-f]{6}", BODY_COLORS[theme])
    assert re.fullmatch(r"#[0-9a-f]{6}", TEXT_COLORS[theme])


def test_unknown_theme_falls_back_to_classic():
    assert body_for("neon") == body_for("classic")
    assert color_for("listening", "neon") == color_for("listening", "classic")


def test_windows_theme_has_its_own_colours():
    assert color_for("listening", "windows") == "#e5719b"


def test_island_themes_match_the_app_themes():
    from friday.theme import THEMES as APP_THEMES

    assert set(THEMES) == set(APP_THEMES)


def test_island_is_centred():
    assert island_position(1920, 120) == (900, 8)


def test_odd_screen_width_rounds_down():
    assert island_position(1921, 120) == (900, 8)


def test_narrow_screen_never_gives_negative_x():
    assert island_position(100, 120) == (0, 8)


def test_custom_margin():
    assert island_position(1000, 100, 20) == (450, 20)


@pytest.mark.parametrize("args", [(0, 120, 8), (1920, 0, 8), (1920, 120, -1)])
def test_bad_values_raise(args):
    with pytest.raises(ValueError):
        island_position(*args)


@pytest.mark.parametrize(
    "state", ["loading", "idle", "listening", "thinking", "speaking", "error"]
)
def test_every_state_has_a_colour(state):
    assert state in STATE_COLORS


def test_colours_are_hex():
    for colour in STATE_COLORS.values():
        assert re.fullmatch(r"#[0-9a-f]{6}", colour)


def test_unknown_state_gets_default():
    assert color_for("dancing") == DEFAULT_COLOR


def test_known_state_gets_its_colour():
    assert color_for("listening") == STATE_COLORS["listening"]


def test_black_theme_has_its_own_colours():
    assert color_for("listening", "black") == "#ff5c9a"
    assert color_for("idle", "black") == "#e6e6e6"


def test_win11_idle_is_blue_and_other_states_are_grey_theme():
    assert color_for("idle", "win11") == "#3aa6d8"
    assert color_for("speaking", "win11") == color_for("speaking", "windows")


def test_short_text_is_unchanged():
    assert clip_text("Привет, как дела?") == "Привет, как дела?"


def test_whitespace_is_collapsed():
    assert clip_text("  один \n два   три ") == "один два три"


def test_empty_text_gives_empty_text():
    assert clip_text("   ") == ""


def test_long_text_keeps_the_end_on_word_starts():
    text = " ".join(["слово"] * 50)
    result = clip_text(text, 20)
    assert result.startswith("…")
    assert len(result) <= 21
    assert all(word == "слово" for word in result[1:].split())


def test_long_text_without_spaces_is_cut_by_characters():
    assert clip_text("а" * 300, 50) == "…" + "а" * 50
