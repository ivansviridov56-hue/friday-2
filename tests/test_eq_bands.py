import pytest

from friday.eq_bands import EqSmoother, band_edges, band_levels

EDGES = band_edges(16, fft_size=4096, sample_rate=96000)


def test_edges_count_and_order():
    assert len(EDGES) == 16
    previous_lo = -1
    for lo, hi in EDGES:
        assert lo < hi
        assert lo >= previous_lo
        assert hi <= 4096 // 2 + 1
        previous_lo = lo


def test_edges_are_wider_for_high_bands():
    first = EDGES[0][1] - EDGES[0][0]
    last = EDGES[-1][1] - EDGES[-1][0]
    assert last > first


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bands": 0},
        {"f_min": 0.0},
        {"f_min": 500.0, "f_max": 100.0},
        {"f_max": 60000.0},
    ],
)
def test_edges_reject_bad_input(kwargs):
    params = {"bands": 8, "fft_size": 4096, "sample_rate": 96000}
    params.update(kwargs)
    with pytest.raises(ValueError):
        band_edges(**params)


def test_band_levels_average_inside_each_band():
    magnitudes = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert band_levels(magnitudes, [(0, 2), (2, 6)]) == [0.5, 3.5]


def test_band_levels_empty_range_is_zero():
    assert band_levels([1.0, 2.0], [(10, 12)]) == [0.0]


def test_silence_gives_zeros():
    smoother = EqSmoother(3)
    assert smoother.update([0.0, 0.0, 0.0], 0.1) == [0.0, 0.0, 0.0]


def test_wrong_length_is_rejected():
    with pytest.raises(ValueError):
        EqSmoother(3).update([1.0, 1.0], 0.1)


def test_zero_dt_changes_nothing():
    smoother = EqSmoother(2)
    smoother.update([1.0, 0.5], 0.05)
    before = smoother.values
    assert smoother.update([0.0, 0.0], 0.0) == before


def test_values_stay_between_zero_and_one():
    smoother = EqSmoother(3)
    for _ in range(50):
        values = smoother.update([5.0, 0.2, 0.0], 0.02)
        assert all(0.0 <= v <= 1.0 for v in values)


def test_quiet_music_is_scaled_up_like_loud_music():
    quiet, loud = EqSmoother(3), EqSmoother(3)
    for _ in range(100):
        q = quiet.update([0.01, 0.005, 0.0025], 0.02)
        loud_values = loud.update([1.0, 0.5, 0.25], 0.02)
    assert q[0] > 0.95 and loud_values[0] > 0.95
    assert 0.45 < q[1] < 0.55
    assert 0.45 < loud_values[1] < 0.55


def _steps_until(smoother, level, condition, dt=0.01, limit=1000):
    for step in range(1, limit + 1):
        if condition(smoother.update([level], dt)[0]):
            return step
    raise AssertionError("condition never reached")


def test_rises_faster_than_it_falls():
    smoother = EqSmoother(1)
    rise = _steps_until(smoother, 1.0, lambda v: v > 0.9)
    fall = _steps_until(smoother, 0.0, lambda v: v < 0.1)
    assert fall > 3 * rise


def test_fades_to_zero_in_silence():
    smoother = EqSmoother(1)
    for _ in range(50):
        smoother.update([1.0], 0.02)
    for _ in range(300):
        smoother.update([0.0], 0.01)
    assert smoother.values[0] < 0.01


def test_gain_adapts_after_a_loud_part():
    smoother = EqSmoother(1)
    for _ in range(50):
        smoother.update([1.0], 0.02)
    for _ in range(50):  # one second of a much quieter sound
        value = smoother.update([0.1], 0.02)[0]
    assert value < 0.3  # the gain still remembers the loud part
    for _ in range(500):  # ten more seconds
        value = smoother.update([0.1], 0.02)[0]
    assert value > 0.95  # now the quiet sound is scaled up
