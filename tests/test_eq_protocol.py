import pytest

from friday.eq_protocol import EQ_BANDS, format_eq, parse_eq


def test_format_scales_to_integers():
    assert format_eq([0, 0.5, 1]) == "0 50 100"


def test_format_clamps_and_cleans_bad_numbers():
    assert format_eq([-1, 2, float("nan"), float("inf")]) == "0 100 0 0"


def test_format_empty_is_empty():
    assert format_eq([]) == ""


def test_parse_gives_levels_between_zero_and_one():
    assert parse_eq("0 50 100", bands=3) == [0.0, 0.5, 1.0]


def test_parse_default_is_sixteen_bands():
    assert EQ_BANDS == 16
    assert parse_eq(" ".join(["10"] * 16)) == [0.1] * 16
    assert parse_eq(" ".join(["10"] * 15)) is None


@pytest.mark.parametrize(
    "arg", ["", "1 2", "1 2 3 4", "1 x 3", "1 2 101", "1 2 -1", "1 2 3.5"]
)
def test_parse_rejects_bad_lines(arg):
    assert parse_eq(arg, bands=3) is None


def test_round_trip():
    levels = [0.0, 0.25, 0.5, 1.0]
    assert parse_eq(format_eq(levels), bands=4) == levels
