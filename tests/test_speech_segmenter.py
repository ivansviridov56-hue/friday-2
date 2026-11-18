import numpy as np
import pytest

from friday.speech_segmenter import SAMPLE_RATE, SpeechSegmenter


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds), dtype=np.float32)


def speech(seconds: float, amplitude: float = 0.1) -> np.ndarray:
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def noise(seconds: float, std: float) -> np.ndarray:
    rng = np.random.default_rng(1)
    return rng.normal(0.0, std, int(SAMPLE_RATE * seconds)).astype(np.float32)


def run(segmenter: SpeechSegmenter, audio: np.ndarray, chunk: int = 480) -> list:
    phrases = []
    for start in range(0, audio.size, chunk):
        phrases += segmenter.feed(audio[start : start + chunk])
    return phrases


def test_silence_gives_no_phrases() -> None:
    assert run(SpeechSegmenter(), silence(3)) == []


def test_one_phrase_is_cut_after_the_pause() -> None:
    audio = np.concatenate([silence(1), speech(1), silence(1.5)])
    phrases = run(SpeechSegmenter(), audio)
    assert len(phrases) == 1
    seconds = phrases[0].size / SAMPLE_RATE
    assert 1.0 <= seconds <= 2.3
    assert float(np.abs(phrases[0]).max()) > 0.09


def test_phrase_starts_with_a_little_audio_before_the_speech() -> None:
    audio = np.concatenate([silence(1), speech(1), silence(1.5)])
    phrase = run(SpeechSegmenter(), audio)[0]
    first_loud = int(np.argmax(np.abs(phrase) > 0.05))
    assert first_loud > int(0.1 * SAMPLE_RATE)


def test_two_phrases_are_two_segments() -> None:
    audio = np.concatenate(
        [silence(0.5), speech(1), silence(1.5), speech(1), silence(1.5)]
    )
    assert len(run(SpeechSegmenter(), audio)) == 2


def test_short_pause_inside_a_phrase_does_not_split_it() -> None:
    audio = np.concatenate(
        [silence(0.5), speech(1), silence(0.4), speech(1), silence(1.5)]
    )
    assert len(run(SpeechSegmenter(), audio)) == 1


def test_short_click_is_dropped() -> None:
    audio = np.concatenate([silence(1), speech(0.06), silence(2)])
    assert run(SpeechSegmenter(), audio) == []


def test_chunk_size_does_not_matter() -> None:
    audio = np.concatenate(
        [silence(1), speech(1), silence(1.5), speech(0.8), silence(1.5)]
    )
    sizes = []
    for chunk in (1, 137, 480, 4000):
        phrases = run(SpeechSegmenter(), audio, chunk=chunk)
        sizes.append([p.size for p in phrases])
    assert len(sizes[0]) == 2
    assert all(s == sizes[0] for s in sizes)


def test_long_monologue_is_cut_at_the_limit() -> None:
    audio = np.concatenate([silence(0.5), speech(5), silence(1.5)])
    phrases = run(SpeechSegmenter(max_phrase_s=2.0), audio)
    assert len(phrases) >= 2
    assert all(p.size / SAMPLE_RATE <= 2.1 for p in phrases)


def test_steady_noise_is_not_speech() -> None:
    assert run(SpeechSegmenter(), noise(4, std=0.02)) == []


def test_long_steady_noise_never_makes_a_phrase() -> None:
    assert run(SpeechSegmenter(), noise(16, std=0.02)) == []


def test_speech_right_at_the_start_does_not_break_later_phrases() -> None:
    audio = np.concatenate([speech(1), silence(2), speech(1), silence(1.5)])
    assert len(run(SpeechSegmenter(), audio)) >= 1


def test_speech_over_noise_is_found() -> None:
    audio = np.concatenate(
        [noise(2, 0.02), speech(1, 0.15) + noise(1, 0.02), noise(1.5, 0.02)]
    )
    assert len(run(SpeechSegmenter(), audio)) == 1


def test_reset_drops_a_phrase_in_progress() -> None:
    segmenter = SpeechSegmenter()
    segmenter.feed(np.concatenate([silence(0.5), speech(1)]))
    assert segmenter.in_speech
    segmenter.reset()
    assert not segmenter.in_speech
    assert segmenter.feed(silence(2)) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sample_rate": 0},
        {"frame_ms": 0},
        {"min_rms": 0},
        {"noise_factor": 0.5},
        {"start_frames": 0},
        {"end_silence_s": 0},
        {"max_phrase_s": 0},
        {"preroll_s": -1},
        {"calibration_s": -1},
    ],
)
def test_bad_settings_are_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        SpeechSegmenter(**kwargs)
