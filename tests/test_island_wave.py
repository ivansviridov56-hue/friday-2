import pytest

from friday.island_logic import (
    LINE_GAP,
    MAX_WAVE_AMPLITUDE,
    STATE_COLORS,
    WAVE_BY_STATE,
    WAVE_PAD,
    WaveParams,
    edge_gap,
    ease_params,
    wave_offset,
    wave_params,
)


def test_wave_is_zero_at_both_ends():
    assert wave_offset(0, 100, 1.3, 2.0, 1.5) == pytest.approx(0, abs=1e-9)
    assert wave_offset(100, 100, 1.3, 2.0, 1.5) == pytest.approx(0, abs=1e-9)


def test_wave_never_exceeds_the_amplitude():
    for phase in (0.0, 1.0, 2.5, 4.0, 6.0):
        for x in range(0, 101, 5):
            assert abs(wave_offset(x, 100, phase, 2.0, 1.5)) <= 2.0 + 1e-9


def test_wave_moves_with_the_phase():
    assert wave_offset(40, 100, 0.0, 2.0, 1.0) != wave_offset(40, 100, 1.0, 2.0, 1.0)


def test_zero_amplitude_gives_a_flat_edge():
    assert wave_offset(40, 100, 1.0, 0.0, 1.0) == 0


def test_wave_rejects_bad_width():
    with pytest.raises(ValueError):
        wave_offset(10, 0, 0.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        edge_gap(10, -5)


def test_x_outside_the_range_is_clamped():
    assert wave_offset(-20, 100, 1.0, 2.0, 1.0) == pytest.approx(0, abs=1e-9)
    assert wave_offset(500, 100, 1.0, 2.0, 1.0) == pytest.approx(0, abs=1e-9)


def test_unknown_state_moves_like_idle():
    assert wave_params("???") == wave_params("idle")


@pytest.mark.parametrize("state", list(STATE_COLORS))
def test_every_state_has_wave_params(state):
    assert state in WAVE_BY_STATE


def test_listening_moves_more_than_idle():
    assert wave_params("listening").amplitude > wave_params("idle").amplitude


def test_no_amplitude_is_above_the_maximum():
    assert all(p.amplitude <= MAX_WAVE_AMPLITUDE for p in WAVE_BY_STATE.values())


def test_pad_has_room_for_wave_line_and_pen():
    assert WAVE_PAD >= MAX_WAVE_AMPLITUDE + LINE_GAP + 2


def test_gap_is_zero_at_the_ends_and_full_in_the_middle():
    assert edge_gap(0, 100) == pytest.approx(0, abs=1e-9)
    assert edge_gap(100, 100) == pytest.approx(0, abs=1e-9)
    assert edge_gap(50, 100) == pytest.approx(LINE_GAP)


def test_ease_params_ends_and_middle():
    a, b = WaveParams(1.0, 2.0, 3.0), WaveParams(3.0, 4.0, 5.0)
    assert ease_params(a, b, 0.0) == a
    assert ease_params(a, b, 1.0) == b
    assert ease_params(a, b, 0.5) == WaveParams(2.0, 3.0, 4.0)


def test_ease_params_rejects_bad_k():
    a = WaveParams(1.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        ease_params(a, a, 1.5)
    with pytest.raises(ValueError):
        ease_params(a, a, -0.1)
