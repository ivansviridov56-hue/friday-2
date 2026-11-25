import pytest

from friday.island_logic import LINE_GAP
from friday.island_shape import FLARE, RADIUS, body_outline, light_line

W, BODY_W, BODY_H = 480, 150, 34
X0 = (W - (BODY_W + 2 * FLARE)) / 2
LEFT = X0 + FLARE
RIGHT = LEFT + BODY_W


def test_outline_starts_and_ends_at_the_top_edge():
    pts = body_outline(W, BODY_W, BODY_H, 0.0, 1.0, 0.0)
    assert pts[0] == pytest.approx((X0, 0))
    assert pts[-1] == pytest.approx((RIGHT + FLARE, 0))


def test_outline_is_symmetric_without_waves():
    pts = body_outline(W, BODY_W, BODY_H, 0.0, 1.0, 0.0)
    for (ax, ay), (bx, by) in zip(pts, reversed(pts)):
        assert ax + bx == pytest.approx(W)
        assert ay == pytest.approx(by)


def test_outline_width_is_the_body_plus_two_flares():
    pts = body_outline(W, BODY_W, BODY_H, 3.0, 1.5, 0.7)
    xs = [x for x, _ in pts]
    assert max(xs) - min(xs) == pytest.approx(BODY_W + 2 * FLARE)


def test_the_corners_meet_the_edge_exactly_at_the_body_bottom():
    pts = body_outline(W, BODY_W, BODY_H, 3.0, 1.5, 0.7)
    ends = [
        p
        for p in pts
        if abs(p[0] - (LEFT + RADIUS)) < 1e-6 or abs(p[0] - (RIGHT - RADIUS)) < 1e-6
    ]
    assert len(ends) == 2
    for _, y in ends:
        assert y == pytest.approx(BODY_H)


def test_waves_move_with_the_phase():
    a = body_outline(W, BODY_W, BODY_H, 3.0, 1.5, 0.0)
    b = body_outline(W, BODY_W, BODY_H, 3.0, 1.5, 1.0)
    assert a != b


def test_without_amplitude_the_phase_changes_nothing():
    a = body_outline(W, BODY_W, BODY_H, 0.0, 1.5, 0.0)
    b = body_outline(W, BODY_W, BODY_H, 0.0, 1.5, 1.0)
    assert a == b


def test_the_wave_stays_within_the_amplitude():
    pts = body_outline(W, BODY_W, BODY_H, 3.0, 1.5, 0.7)
    assert max(y for _, y in pts) <= BODY_H + 3.0 + 1e-9


def test_light_line_floats_above_the_edge():
    pts = light_line(W, BODY_W, BODY_H, 0.0, 1.0, 0.0)
    assert pts[0][1] == pytest.approx(BODY_H)
    assert pts[-1][1] == pytest.approx(BODY_H)
    assert min(y for _, y in pts) == pytest.approx(BODY_H - LINE_GAP)
    assert pts[0][0] == pytest.approx(LEFT + RADIUS)
    assert pts[-1][0] == pytest.approx(RIGHT - RADIUS)


def test_window_must_fit_the_body_and_the_flares():
    with pytest.raises(ValueError):
        body_outline(100, BODY_W, BODY_H, 0.0, 1.0, 0.0)


def test_body_must_be_wider_than_its_corners():
    with pytest.raises(ValueError):
        body_outline(W, 20, BODY_H, 0.0, 1.0, 0.0)
