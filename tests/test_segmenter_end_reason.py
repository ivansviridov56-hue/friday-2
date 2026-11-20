import numpy as np

from friday.speech_segmenter import SAMPLE_RATE, SpeechSegmenter


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds), dtype=np.float32)


def speech(seconds: float, amplitude: float = 0.1) -> np.ndarray:
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def run(segmenter: SpeechSegmenter, audio: np.ndarray) -> list:
    phrases = []
    for start in range(0, audio.size, 480):
        phrases += segmenter.feed(audio[start : start + 480])
    return phrases


def test_no_phrase_no_end_info() -> None:
    segmenter = SpeechSegmenter()
    run(segmenter, silence(2))
    assert segmenter.last_end is None


def test_pause_ends_a_phrase_with_reason_silence() -> None:
    segmenter = SpeechSegmenter()
    run(segmenter, np.concatenate([silence(0.5), speech(1), silence(1.5)]))
    assert segmenter.last_end is not None
    assert segmenter.last_end.reason == "silence"


def test_limit_ends_a_phrase_with_reason_max() -> None:
    segmenter = SpeechSegmenter(max_phrase_s=2.0)
    run(segmenter, np.concatenate([silence(0.5), speech(5)]))
    assert segmenter.last_end is not None
    assert segmenter.last_end.reason == "max"


def test_end_info_carries_threshold_and_floor() -> None:
    segmenter = SpeechSegmenter()
    run(segmenter, np.concatenate([silence(0.5), speech(1), silence(1.5)]))
    info = segmenter.last_end
    assert info is not None
    assert info.threshold >= 0.004
    assert info.floor >= 0.0


def test_a_dropped_click_still_records_its_end() -> None:
    segmenter = SpeechSegmenter()
    assert run(segmenter, np.concatenate([silence(1), speech(0.06), silence(2)])) == []
    assert segmenter.last_end is not None
