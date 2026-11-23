import pytest

from friday.theme import THEMES
from friday.transparency import (
    DEFAULT_PERCENT,
    clean_percents,
    default_percent,
    parse_percent,
    percent_for,
)


def test_every_theme_has_a_default():
    assert set(DEFAULT_PERCENT) == set(THEMES)


def test_win11_default_matches_the_old_60_percent_tint():
    assert default_percent("win11") == 40


@pytest.mark.parametrize("theme", ["classic", "windows", "black"])
def test_other_themes_start_opaque(theme):
    assert default_percent(theme) == 0


def test_unknown_theme_default_is_opaque():
    assert default_percent("pink") == 0


@pytest.mark.parametrize(
    "value, expected", [(0, 0), (40, 40), (100, 100), (40.0, 40), (40.6, 41)]
)
def test_parse_percent_accepts(value, expected):
    assert parse_percent(value) == expected


@pytest.mark.parametrize(
    "value",
    [-1, 101, 100.6, float("nan"), float("inf"), True, "40", None, [40]],
)
def test_parse_percent_rejects(value):
    assert parse_percent(value) is None


def test_clean_percents_keeps_only_known_themes_and_valid_values():
    raw = {"classic": 20, "win11": 150, "pink": 10, "black": "5", "windows": 100}
    assert clean_percents(raw) == {"classic": 20, "windows": 100}


@pytest.mark.parametrize("raw", [None, [], "x", 5])
def test_clean_percents_non_mapping_gives_empty(raw):
    assert clean_percents(raw) == {}


def test_percent_for_uses_saved_value():
    assert percent_for("win11", {"win11": 70}) == 70


def test_percent_for_falls_back_to_default():
    assert percent_for("win11", {}) == 40
    assert percent_for("black", {"black": 500}) == 0
