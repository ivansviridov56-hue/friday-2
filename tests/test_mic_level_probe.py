import numpy as np
import pytest

from friday.mic_level_probe import (
    FRAME_MS,
    build_report,
    frame_levels,
    listen_for,
    phrase_lengths,
    verdict,
)
from friday.speech_segmenter import SAMPLE_RATE


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds), dtype=np.float32)


def tone(seconds: float, amplitude: float = 0.1) -> np.ndarray:
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def noise(seconds: float, std: float) -> np.ndarray:
    rng = np.random.default_rng(1)
    return rng.normal(0.0, std, int(SAMPLE_RATE * seconds)).astype(np.float32)


class FakeMic:
    def __init__(self, frames: list[np.ndarray]) -> None:
        self._frames = frames
        self.listeners: list = []

    def add_listener(self, listener) -> None:
        self.listeners.append(listener)

    def remove_listener(self, listener) -> None:
        self.listeners.remove(listener)

    def emit_all(self) -> None:
        for frame in self._frames:
            for listener in list(self.listeners):
                listener(frame)


def test_frame_levels_of_a_constant_signal() -> None:
    audio = np.full(SAMPLE_RATE, 0.5, dtype=np.float32)
    levels = frame_levels(audio)
    assert levels.size == SAMPLE_RATE // (SAMPLE_RATE * FRAME_MS // 1000)
    assert np.allclose(levels, 0.5)


def test_frame_levels_ignores_the_incomplete_tail() -> None:
    size = SAMPLE_RATE * FRAME_MS // 1000
    assert frame_levels(np.ones(size * 3 + 10, dtype=np.float32)).size == 3


def test_frame_levels_of_too_little_audio_is_empty() -> None:
    assert frame_levels(np.ones(10, dtype=np.float32)).size == 0


def test_report_needs_audio() -> None:
    with pytest.raises(ValueError):
        build_report(np.zeros(0, dtype=np.float32), tone(1))


def test_quiet_room_and_clear_speech_is_ok() -> None:
    report = build_report(noise(5, 0.003), tone(5, 0.1))
    assert report.noise_over == 0.0
    assert verdict(report).startswith("ОК")


def test_quiet_lavalier_in_a_quiet_room_is_ok() -> None:
    # real numbers from the first live run: background ~0.0001, quiet speech ~0.013
    report = build_report(noise(5, 0.0001), tone(5, 0.018))
    assert report.threshold == pytest.approx(0.004)
    assert verdict(report).startswith("ОК")


def test_dead_microphone_is_reported() -> None:
    report = build_report(silence(5), silence(5))
    assert verdict(report).startswith("НЕТ ЗВУКА")


def test_noise_that_comes_and_goes_is_a_warning_not_a_failure() -> None:
    # music or a TV: quiet most of the time, with loud bursts
    room = np.concatenate([noise(4, 0.003), tone(1, 0.05)])
    report = build_report(room, tone(5, 0.1))
    assert report.noise_over > 0.1
    assert verdict(report).startswith("ВНИМАНИЕ")
    assert "вариант B" not in verdict(report)


def test_steady_loud_noise_is_absorbed_by_the_adaptive_threshold() -> None:
    report = build_report(noise(5, 0.05), tone(5, 0.4))
    assert report.noise_over < 0.01
    assert verdict(report).startswith("ОК")


def test_speech_barely_above_steady_noise_is_a_problem() -> None:
    report = build_report(noise(5, 0.05), tone(5, 0.1))
    assert verdict(report).startswith("ПРОБЛЕМА: твоя речь")


def test_speech_below_the_threshold_is_a_problem() -> None:
    report = build_report(noise(5, 0.0001), tone(5, 0.004))
    assert verdict(report).startswith("ПРОБЛЕМА: твоя речь")


def test_pauses_between_phrases_do_not_count_against_the_speaker() -> None:
    # 12 s with only 4 s of speech: the old share-of-frames rule called this a failure
    audio = np.concatenate([tone(2, 0.05), silence(4), tone(2, 0.05), silence(4)])
    report = build_report(noise(5, 0.0001), audio)
    assert verdict(report).startswith("ОК")


def test_listen_for_collects_frames_and_unsubscribes() -> None:
    mic = FakeMic([np.ones(10, dtype=np.float32), np.ones(5, dtype=np.float32)])
    audio = listen_for(mic, 3, sleep=lambda s: mic.emit_all())
    assert audio.shape == (15,)
    assert mic.listeners == []


def test_listen_for_without_frames_is_empty() -> None:
    mic = FakeMic([])
    assert listen_for(mic, 3, sleep=lambda s: None).size == 0


def test_listen_for_unsubscribes_when_interrupted() -> None:
    mic = FakeMic([])

    def sleep(_: float) -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        listen_for(mic, 3, sleep=sleep)
    assert mic.listeners == []


def test_phrase_lengths_finds_each_phrase() -> None:
    audio = np.concatenate([silence(0.5), tone(1), silence(1.5), tone(1), silence(1.5)])
    lengths = phrase_lengths(audio)
    assert len(lengths) == 2
    assert all(1.0 <= length <= 2.3 for length in lengths)


def test_phrase_lengths_of_silence_is_empty() -> None:
    assert phrase_lengths(silence(3)) == []
