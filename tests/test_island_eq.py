import pytest

from friday.island_eq import EQ_AMPLITUDE, eq_offset, eq_value

ALL = [1.0] * 16


def test_value_follows_the_bands_and_is_smooth_between_them():
    levels = [0.2, 0.8]
    assert eq_value(0.25, levels) == pytest.approx(0.2)
    assert eq_value(0.75, levels) == pytest.approx(0.8)
    assert eq_value(0.5, levels) == pytest.approx(0.5)


def test_value_outside_the_edge_and_odd_inputs():
    assert eq_value(-1, [0.3, 0.9]) == pytest.approx(0.3)
    assert eq_value(2, [0.3, 0.9]) == pytest.approx(0.9)
    assert eq_value(0.5, []) == 0.0
    assert eq_value(0.5, [0.7]) == 0.7


def test_offset_is_zero_at_both_ends():
    assert eq_offset(0, 100, ALL) == 0.0
    assert eq_offset(100, 100, ALL) == 0.0


def test_offset_in_the_middle_is_the_full_amplitude():
    assert eq_offset(50, 100, ALL) == pytest.approx(EQ_AMPLITUDE)


def test_offset_scales_with_the_level():
    assert eq_offset(50, 100, [0.5] * 16) == pytest.approx(EQ_AMPLITUDE / 2)
    assert eq_offset(50, 100, [0.0] * 16) == 0.0
    assert eq_offset(50, 100, []) == 0.0


def test_offset_never_leaves_the_amplitude():
    levels = [0.0, 3.0, -2.0, 1.0] * 4
    for x in range(0, 101, 5):
        assert 0.0 <= eq_offset(x, 100, levels) <= EQ_AMPLITUDE


def test_symmetric_levels_give_a_symmetric_edge():
    levels = [0.1, 0.5, 0.9, 0.9, 0.5, 0.1]
    assert eq_offset(30, 100, levels) == pytest.approx(eq_offset(70, 100, levels))


def test_width_must_be_positive():
    with pytest.raises(ValueError):
        eq_offset(1, 0, ALL)
