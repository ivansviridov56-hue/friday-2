import math

from friday.island_looks import DEFAULT_LOOK, LOOKS, look_shapes

STATES = ("idle", "listening", "thinking", "speaking", "loading", "error")


def test_blobs_is_a_look_and_dot_stays_the_default():
    assert "blobs" in LOOKS
    assert DEFAULT_LOOK == "dot"


def test_blobs_are_three_circles():
    shapes = look_shapes("blobs", "idle", 0.0)
    assert len(shapes) == 3
    for _cx, _cy, w, h, radius in shapes:
        assert w == h
        assert math.isclose(radius, w / 2)


def test_blobs_stay_inside_the_icon_area_in_every_state():
    for state in STATES:
        for step in range(200):
            for cx, cy, w, _h, _r in look_shapes("blobs", state, step * 0.1, 1.0):
                assert abs(cx) + w / 2 <= 20.0
                assert abs(cy) + w / 2 <= 20.0


def test_blobs_move_in_idle():
    assert look_shapes("blobs", "idle", 0.0) != look_shapes("blobs", "idle", 1.0)


def test_blobs_stand_still_on_error():
    assert look_shapes("blobs", "error", 0.0) == look_shapes("blobs", "error", 5.0)


def test_blobs_are_smaller_on_error_than_in_idle():
    error = sum(s[2] for s in look_shapes("blobs", "error", 0.0))
    idle = sum(s[2] for s in look_shapes("blobs", "idle", 0.0))
    assert error < idle


def test_pulse_makes_blobs_bigger():
    quiet = look_shapes("blobs", "speaking", 0.0, 0.0)
    loud = look_shapes("blobs", "speaking", 0.0, 1.0)
    assert all(l[2] > q[2] for q, l in zip(quiet, loud))


def test_pulse_is_clamped():
    assert look_shapes("blobs", "speaking", 0.0, 5.0) == look_shapes(
        "blobs", "speaking", 0.0, 1.0
    )
