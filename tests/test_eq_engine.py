import pytest

np = pytest.importorskip("numpy")

from friday.eq_bands import band_edges  # noqa: E402
from friday.eq_engine import EqEngine, window_size  # noqa: E402

RATE = 96000


def _stereo(freq, seconds=0.2, amplitude=0.5, rate=RATE):
    t = np.arange(int(rate * seconds)) / rate
    mono = (amplitude * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    return np.repeat(mono, 2).tobytes()  # left, right, left, right ...


def _settle(engine, steps=60):
    levels = []
    for _ in range(steps):
        levels = engine.levels(0.02)
    return levels


def test_window_follows_the_sample_rate():
    assert window_size(96000) == 8192
    assert window_size(48000) == 4096
    assert EqEngine(96000, 2).fft_size == 8192


def test_silence_gives_zeros():
    engine = EqEngine(RATE, 2)
    assert engine.levels(0.02) == [0.0] * 16
    engine.feed(bytes(4 * 4096))
    assert _settle(engine) == [0.0] * 16


def test_a_tone_lights_up_its_own_band():
    engine = EqEngine(RATE, 2)
    engine.feed(_stereo(1000))
    levels = _settle(engine)
    edges = band_edges(16, engine.fft_size, RATE)
    bin_of_tone = round(1000 * engine.fft_size / RATE)
    expected = next(i for i, (lo, hi) in enumerate(edges) if lo <= bin_of_tone < hi)
    assert levels.index(max(levels)) == expected
    assert levels[expected] > 0.95
    assert all(0.0 <= v <= 1.0 for v in levels)


def test_small_blocks_add_up_like_one_big_block():
    raw = _stereo(1000)
    whole, parts = EqEngine(RATE, 2), EqEngine(RATE, 2)
    whole.feed(raw)
    step = 1024 * 4  # 1024 frames of 16-bit stereo
    for start in range(0, len(raw), step):
        parts.feed(raw[start : start + step])
    assert _settle(whole) == pytest.approx(_settle(parts))


def test_the_bars_fall_when_the_sound_stops():
    engine = EqEngine(RATE, 2)
    engine.feed(_stereo(1000))
    _settle(engine)
    engine.feed(bytes(4 * 20000))
    assert max(_settle(engine, steps=300)) < 0.01


def test_bass_and_treble_both_show_up():
    engine = EqEngine(RATE, 2)
    mixed = np.frombuffer(_stereo(100), dtype=np.int16).astype(np.int32)
    mixed = mixed + np.frombuffer(_stereo(8000), dtype=np.int16)
    engine.feed(np.clip(mixed, -32768, 32767).astype(np.int16).tobytes())
    levels = _settle(engine)
    edges = band_edges(16, engine.fft_size, RATE)

    def band_of(freq):
        b = round(freq * engine.fft_size / RATE)
        return next(i for i, (lo, hi) in enumerate(edges) if lo <= b < hi)

    low, high = levels[band_of(100)], levels[band_of(8000)]
    assert min(low, high) / max(low, high) > 0.4
