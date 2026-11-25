import pytest

from friday.island_looks import (
    BARS,
    BAR_MAX,
    BAR_MIN,
    BAR_STEP,
    BLINK_PERIOD,
    BLINK_SECONDS,
    DEFAULT_LOOK,
    LOOKS,
    look_or_default,
    look_shapes,
)

STATES = ["idle", "listening", "thinking", "speaking", "loading", "error"]


def times():
    return [i * 0.137 for i in range(200)]


def test_the_known_looks():
    assert set(LOOKS) == {"dot", "eyes", "equalizer"}
    assert DEFAULT_LOOK == "dot"


def test_look_or_default():
    assert look_or_default("eyes") == "eyes"
    assert look_or_default("nope") == DEFAULT_LOOK
    assert look_or_default("") == DEFAULT_LOOK
    assert look_or_default(None) == DEFAULT_LOOK


def test_an_unknown_look_raises():
    with pytest.raises(ValueError):
        look_shapes("nope", "idle", 0.0)


# ---- dot ----
def test_dot_is_one_centred_circle():
    ((cx, cy, w, h, r),) = look_shapes("dot", "idle", 0.0)
    assert (cx, cy) == (0.0, 0.0)
    assert w == h == 2 * r


def test_dot_grows_with_the_pulse():
    small = look_shapes("dot", "speaking", 0.0, 0.0)[0][2]
    big = look_shapes("dot", "speaking", 0.0, 1.0)[0][2]
    assert big > small


def test_dot_pulse_is_clamped():
    assert look_shapes("dot", "idle", 0.0, 5.0) == look_shapes("dot", "idle", 0.0, 1.0)


# ---- eyes ----
def test_two_eyes_mirror_each_other():
    left, right = look_shapes("eyes", "idle", 2.0)
    assert left[0] == pytest.approx(-right[0])
    assert left[1:] == right[1:]


def test_eyes_are_open_between_blinks():
    open_h = look_shapes("eyes", "idle", BLINK_PERIOD / 2)[0][3]
    assert open_h == pytest.approx(9.0)


def test_eyes_close_when_blinking():
    open_h = look_shapes("eyes", "idle", BLINK_PERIOD / 2)[0][3]
    closed_h = look_shapes("eyes", "idle", BLINK_SECONDS / 2)[0][3]
    assert closed_h < 0.3 * open_h


def test_a_blink_repeats_every_period():
    a = look_shapes("eyes", "idle", BLINK_SECONDS / 2)
    b = look_shapes("eyes", "idle", BLINK_SECONDS / 2 + BLINK_PERIOD)
    assert a == b


def test_listening_eyes_are_wider_open_and_never_blink():
    heights = {look_shapes("eyes", "listening", t)[0][3] for t in times()}
    assert len(heights) == 1
    assert heights.pop() > look_shapes("eyes", "idle", BLINK_PERIOD / 2)[0][3]


def test_thinking_eyes_look_up_and_sway():
    ys = {round(s[1], 6) for t in times() for s in look_shapes("eyes", "thinking", t)}
    xs = {round(look_shapes("eyes", "thinking", t)[0][0], 3) for t in times()}
    assert ys == {-2.0}
    assert len(xs) > 5


def test_speaking_eyes_grow_with_the_pulse():
    t = BLINK_PERIOD / 2
    small = look_shapes("eyes", "speaking", t, 0.0)[0][3]
    big = look_shapes("eyes", "speaking", t, 1.0)[0][3]
    assert big > small


# ---- equalizer ----
def test_equalizer_has_evenly_spaced_centred_bars():
    bars = look_shapes("equalizer", "speaking", 1.0)
    assert len(bars) == BARS
    xs = [b[0] for b in bars]
    assert sum(xs) == pytest.approx(0.0)
    assert [round(b - a, 6) for a, b in zip(xs, xs[1:])] == [BAR_STEP] * (BARS - 1)


@pytest.mark.parametrize("state", STATES)
def test_bar_heights_stay_in_range(state):
    for t in times():
        for _, _, _, h, _ in look_shapes("equalizer", state, t):
            assert BAR_MIN - 1e-9 <= h <= BAR_MAX + 1e-9


def _average(state):
    values = [b[3] for t in times() for b in look_shapes("equalizer", state, t)]
    return sum(values) / len(values)


def test_speaking_moves_more_than_idle():
    assert _average("speaking") > _average("idle")
    assert _average("listening") > _average("idle")


def test_the_bars_move_with_time():
    a = look_shapes("equalizer", "listening", 1.0)
    b = look_shapes("equalizer", "listening", 1.3)
    assert a != b


# ---- all looks ----
@pytest.mark.parametrize("look", LOOKS)
@pytest.mark.parametrize("state", STATES + ["something-new"])
def test_every_shape_is_drawable(look, state):
    for t in times():
        for cx, cy, w, h, r in look_shapes(look, state, t, 0.5):
            assert w > 0 and h > 0
            assert 0 <= r <= min(w, h) / 2 + 1e-9
