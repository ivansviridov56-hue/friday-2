"""Probe for stage 11c-3: how loud are silence and speech on the real microphone?

Run: python -m friday.mic_level_probe
Close the assistant first (it holds the microphone). Nothing is saved to disk.
Audio comes through Recorder.add_listener, so this also checks the subscription
live. The script measures the room, measures your speech, then runs the speech
segmenter over both recordings and tells whether the energy detector will work.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from friday.speech_segmenter import (
    DEFAULT_MIN_RMS,
    DEFAULT_NOISE_FACTOR,
    SAMPLE_RATE,
    SpeechSegmenter,
)

log = logging.getLogger(__name__)

FRAME_MS = 30
SILENCE_SECONDS = 5
SPEECH_SECONDS = 12
NOISY_SHARE = 0.01  # more silence frames than this above the threshold: extra phrases
MIN_SPEECH_MARGIN = (
    1.5  # loud speech (90th percentile) must be this many times the threshold
)
DEAD_LEVEL = 0.0002  # speech never louder than this: the microphone is off or muted


class Listenable(Protocol):
    def add_listener(self, listener: Callable[[np.ndarray], object]) -> None: ...

    def remove_listener(self, listener: Callable[[np.ndarray], object]) -> None: ...


@dataclass(frozen=True)
class LevelReport:
    noise_median: float
    noise_p95: float
    speech_p50: float
    speech_p90: float
    threshold: float  # what the segmenter would use for this room
    noise_over: float  # share of silence frames above the threshold


def frame_levels(
    audio: np.ndarray, sample_rate: int = SAMPLE_RATE, frame_ms: int = FRAME_MS
) -> np.ndarray:
    """RMS level of every whole frame of the audio."""
    size = sample_rate * frame_ms // 1000
    count = audio.size // size
    if count == 0:
        return np.zeros(0, dtype=np.float32)
    frames = np.asarray(audio, dtype=np.float32)[: count * size].reshape(count, size)
    return np.sqrt(np.mean(frames * frames, axis=1))


def build_report(
    silence: np.ndarray,
    speech: np.ndarray,
    min_rms: float = DEFAULT_MIN_RMS,
    noise_factor: float = DEFAULT_NOISE_FACTOR,
) -> LevelReport:
    quiet = frame_levels(silence)
    loud = frame_levels(speech)
    if quiet.size == 0 or loud.size == 0:
        raise ValueError("need some audio for both silence and speech")
    median = float(np.median(quiet))
    threshold = max(min_rms, median * noise_factor)
    return LevelReport(
        noise_median=median,
        noise_p95=float(np.percentile(quiet, 95)),
        speech_p50=float(np.percentile(loud, 50)),
        speech_p90=float(np.percentile(loud, 90)),
        threshold=threshold,
        noise_over=float(np.mean(quiet > threshold)),
    )


def verdict(report: LevelReport) -> str:
    """One line: will the energy detector cope with this room and this microphone?"""
    if report.speech_p90 < DEAD_LEVEL:
        return "НЕТ ЗВУКА: микрофон выключен или молчит. Проверь и повтори."
    if report.speech_p90 < report.threshold * MIN_SPEECH_MARGIN:
        return (
            "ПРОБЛЕМА: твоя речь лишь немного выше порога. Говори ближе к "
            "микрофону или снизим min_rms."
        )
    if report.noise_over > NOISY_SHARE:
        return (
            "ВНИМАНИЕ: фон (музыка? телевизор?) иногда выше порога: будут лишние "
            "фразы на распознавание. Ложных команд это не даёт (нужно имя), но "
            "нагружает видеокарту. Смотри на живом слушателе."
        )
    return "ОК: фон ниже порога, речь заметно выше. Энергетический детектор подходит."


def listen_for(
    recorder: Listenable, seconds: float, sleep: Callable[[float], object] = time.sleep
) -> np.ndarray:
    """Collect everything the microphone hears for a fixed time."""
    frames: list[np.ndarray] = []
    listener = frames.append
    recorder.add_listener(listener)
    try:
        sleep(seconds)
    finally:
        recorder.remove_listener(listener)
    if not frames:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(frames)


def phrase_lengths(audio: np.ndarray, chunk: int = 480) -> list[float]:
    """Run the segmenter over the audio; return the length of each phrase in seconds."""
    segmenter = SpeechSegmenter()
    lengths: list[float] = []
    for start in range(0, audio.size, chunk):
        for phrase in segmenter.feed(audio[start : start + chunk]):
            lengths.append(round(phrase.size / SAMPLE_RATE, 1))
    return lengths


def main() -> None:
    from friday.recorder import Recorder

    logging.basicConfig(level=logging.WARNING)
    recorder = Recorder()
    recorder.open()
    try:
        input(
            f"\n1/2. Тишина: Enter, потом {SILENCE_SECONDS} с молчи "
            "(как будто ты не рядом, фон комнаты): "
        )
        silence = listen_for(recorder, SILENCE_SECONDS)
        input(
            f"\n2/2. Речь: Enter, потом {SPEECH_SECONDS} с говори как с ассистентом, "
            "с паузами между фразами (например три-четыре разные фразы): "
        )
        speech = listen_for(recorder, SPEECH_SECONDS)
    finally:
        recorder.close()

    if silence.size == 0 or speech.size == 0:
        print("Звук не пришёл: подписка на микрофон не получила ни одного кадра.")
        return
    report = build_report(silence, speech)
    print(f"\nфон:   медиана {report.noise_median:.4f}, 95% {report.noise_p95:.4f}")
    print(f"речь:  медиана {report.speech_p50:.4f}, 90% {report.speech_p90:.4f}")
    print(f"порог сегментера для этой комнаты: {report.threshold:.4f}")
    print(f"кадров тишины выше порога: {report.noise_over:.1%}")
    print(f"фраз найдено в тишине: {phrase_lengths(silence)} (ждём [])")
    print(f"фраз найдено в речи:   {phrase_lengths(speech)} (секунды, ждём несколько)")
    print("\n" + verdict(report))


if __name__ == "__main__":
    main()
