import pytest

from friday.island_logic import smoothstep, step_toward


def test_smoothstep_ends_and_middle():
    assert smoothstep(0.0) == 0.0
    assert smoothstep(1.0) == 1.0
    assert smoothstep(0.5) == pytest.approx(0.5)


def test_smoothstep_clamps_and_is_slow_at_the_ends():
    assert smoothstep(-1.0) == 0.0
    assert smoothstep(2.0) == 1.0
    assert smoothstep(0.1) < 0.1


def test_step_toward_moves_by_dt_over_duration():
    assert step_toward(0.0, 1.0, 0.1, 0.4) == pytest.approx(0.25)
    assert step_toward(1.0, 0.0, 0.1, 0.4) == pytest.approx(0.75)


def test_step_toward_does_not_overshoot():
    assert step_toward(0.9, 1.0, 1.0, 0.4) == 1.0
    assert step_toward(0.1, 0.0, 1.0, 0.4) == 0.0


def test_step_toward_without_time_stays():
    assert step_toward(0.3, 1.0, 0.0, 0.4) == 0.3


def test_step_toward_with_no_duration_jumps():
    assert step_toward(0.3, 1.0, 0.016, 0.0) == 1.0
