import pytest

np = pytest.importorskip("numpy")

from friday.eq_bands import band_edges, band_levels  # noqa: E402
from friday.spectrum import hann_window, magnitudes, to_mono  # noqa: E402

RATE = 96000
SIZE = 4096


def _sine(freq, amplitude=0.5):
    t = np.arange(SIZE) / RATE
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_to_mono_averages_channels():
    raw = np.array([16384, -16384, 16384, 16384], dtype=np.int16).tobytes()
    assert to_mono(raw, 2).tolist() == [0.0, 0.5]


def test_to_mono_single_channel_is_scaled_to_one():
    raw = np.array([-32768, 16384], dtype=np.int16).tobytes()
    assert to_mono(raw, 1).tolist() == [-1.0, 0.5]


def test_to_mono_drops_an_incomplete_frame():
    raw = np.array([1000, 1000, 1000, 1000, 1000], dtype=np.int16).tobytes()
    assert len(to_mono(raw, 2)) == 2


def test_to_mono_empty_input():
    assert len(to_mono(b"", 2)) == 0


def test_to_mono_rejects_zero_channels():
    with pytest.raises(ValueError):
        to_mono(b"\x00\x00", 0)


def test_magnitudes_length_is_half_plus_one():
    result = magnitudes(_sine(1000), hann_window(SIZE))
    assert len(result) == SIZE // 2 + 1


def test_silence_has_no_magnitude():
    result = magnitudes(np.zeros(SIZE, dtype=np.float32), hann_window(SIZE))
    assert float(result.max()) == 0.0


def test_window_must_match_the_block():
    with pytest.raises(ValueError):
        magnitudes(_sine(1000), hann_window(SIZE // 2))


def test_a_tone_lights_up_its_own_band():
    edges = band_edges(16, SIZE, RATE)
    levels = band_levels(magnitudes(_sine(1000), hann_window(SIZE)), edges)
    peak_bin = round(1000 * SIZE / RATE)
    expected = next(i for i, (lo, hi) in enumerate(edges) if lo <= peak_bin < hi)
    assert levels.index(max(levels)) == expected


def test_louder_tone_gives_proportionally_larger_magnitude():
    window = hann_window(SIZE)
    loud = magnitudes(_sine(1000, 0.5), window).max()
    quiet = magnitudes(_sine(1000, 0.25), window).max()
    assert float(loud / quiet) == pytest.approx(2.0, rel=0.01)
