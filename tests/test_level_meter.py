import numpy as np
import pytest

from friday.level_meter import LevelMeter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def frame(amplitude: float, size: int = 480) -> np.ndarray:
    return np.full(size, amplitude, dtype=np.float32)


def make() -> tuple[LevelMeter, FakeClock]:
    clock = FakeClock()
    return LevelMeter(clock=clock), clock


def test_nothing_is_emitted_before_the_interval():
    meter, clock = make()
    assert meter.feed(frame(0.05)) is None
    clock.now = 0.02
    assert meter.feed(frame(0.05)) is None


def test_silence_gives_zero():
    meter, clock = make()
    clock.now = 0.06
    assert meter.feed(frame(0.0)) == 0.0


def test_noise_below_the_gate_gives_zero():
    meter, clock = make()
    clock.now = 0.06
    assert meter.feed(frame(0.002)) == pytest.approx(0.0, abs=1e-6)


def test_loud_sound_rises_step_by_step():
    meter, clock = make()
    clock.now = 0.06
    first = meter.feed(frame(0.05))
    clock.now = 0.12
    second = meter.feed(frame(0.05))
    assert first == pytest.approx(0.7, abs=0.01)
    assert second == pytest.approx(0.91, abs=0.01)


def test_level_never_exceeds_one():
    meter, clock = make()
    last = 0.0
    for step in range(1, 30):
        clock.now = step * 0.06
        last = meter.feed(frame(1.0))
        assert last is not None
        assert 0.0 <= last <= 1.0
    assert last > 0.99


def test_level_falls_slowly_after_the_sound_stops():
    meter, clock = make()
    clock.now = 0.06
    loud = meter.feed(frame(0.05))
    assert loud is not None
    clock.now = 0.12
    after = meter.feed(frame(0.0))
    assert after is not None
    assert 0.0 < after < loud
    assert after == pytest.approx(0.525, abs=0.01)


def test_level_is_averaged_over_all_frames_since_the_last_emit():
    meter, clock = make()
    assert meter.feed(frame(0.03)) is None
    clock.now = 0.06
    level = meter.feed(frame(0.0))
    assert level == pytest.approx(0.262, abs=0.01)


def test_empty_frame_is_ignored():
    meter, clock = make()
    clock.now = 0.06
    assert meter.feed(np.array([], dtype=np.float32)) is None


def test_reset_starts_from_zero():
    meter, clock = make()
    clock.now = 0.06
    meter.feed(frame(0.05))
    meter.reset()
    clock.now = 0.12
    assert meter.feed(frame(0.0)) == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"gate": -0.1},
        {"gate": 0.05, "full": 0.05},
        {"interval": 0.0},
        {"attack": 0.0},
        {"release": 1.5},
    ],
)
def test_bad_settings_are_rejected(kwargs):
    with pytest.raises(ValueError):
        LevelMeter(**kwargs)
