import pytest

from friday.island_logic import WAVE_EASE_RATE, blend_factor


def test_matches_the_old_fixed_step_at_62_fps():
    assert blend_factor(0.016, WAVE_EASE_RATE) == pytest.approx(0.06, abs=0.002)


def test_no_time_or_negative_time_moves_nothing():
    assert blend_factor(0.0, WAVE_EASE_RATE) == 0.0
    assert blend_factor(-1.0, WAVE_EASE_RATE) == 0.0


def test_non_positive_rate_moves_nothing():
    assert blend_factor(0.016, 0.0) == 0.0


def test_never_overshoots_after_a_long_pause():
    value = blend_factor(10.0, WAVE_EASE_RATE)
    assert 0.99 < value <= 1.0


def test_independent_of_frame_rate():
    one_step = blend_factor(0.016, WAVE_EASE_RATE)
    two_steps = 1.0 - (1.0 - blend_factor(0.008, WAVE_EASE_RATE)) ** 2
    assert two_steps == pytest.approx(one_step)
