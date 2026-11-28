import pytest

from friday.island_eq import EQ_AMPLITUDE
from friday.island_logic import LINE_GAP
from friday.island_shape import body_outline, light_line

W, BODY_W, BODY_H = 200, 150, 34
FLAT = (W, BODY_W, BODY_H, 0.0, 1.0, 0.0)
ALL = [1.0] * 16


def _lowest(points):
    return max(y for _, y in points)


def test_without_the_equalizer_nothing_changes():
    wave = (W, BODY_W, BODY_H, 2.0, 1.5, 0.7)
    assert body_outline(*wave, eq=ALL, eq_mix=0.0) == body_outline(*wave)
    assert body_outline(*wave, eq=[], eq_mix=1.0) == body_outline(*wave)
    assert light_line(*wave, eq=ALL, eq_mix=0.0) == light_line(*wave)


def test_the_equalizer_pushes_the_edge_down():
    low = _lowest(body_outline(*FLAT, eq=ALL, eq_mix=1.0))
    assert low == pytest.approx(BODY_H + EQ_AMPLITUDE)


def test_the_blend_goes_halfway():
    low = _lowest(body_outline(*FLAT, eq=ALL, eq_mix=0.5))
    assert low == pytest.approx(BODY_H + EQ_AMPLITUDE / 2)


def test_the_light_line_follows_the_equalizer():
    line = light_line(*FLAT, eq=ALL, eq_mix=1.0)
    assert line[len(line) // 2][1] == pytest.approx(BODY_H + EQ_AMPLITUDE - LINE_GAP)


def test_the_equalizer_keeps_the_outline_size():
    assert len(body_outline(*FLAT, eq=ALL, eq_mix=1.0)) == len(body_outline(*FLAT))
