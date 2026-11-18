"""Probe for stage 11a: how does Whisper hear the wake word "Пятница"?

Run: python -m friday.wake_probe
Close the assistant first (it holds the microphone). Nothing is saved to disk.
The script records short clips, prints what Whisper heard and counts the hits.
At the end it records a stretch of ordinary speech without the name to look for
false alarms.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np

log = logging.getLogger(__name__)

WAKE_STEM = "пятниц"
REPEATS = 2
NEGATIVE_SECONDS = 45
SCENARIOS = (
    ("тихо: «Пятница»", 4),
    ("обычным голосом: «Пятница»", 4),
    ("громко: «Пятница!»", 4),
    ("в начале: «Пятница, что на экране»", 5),
    ("в середине: «Слушай, Пятница, включи музыку»", 5),
    ("в конце: «Включи музыку, Пятница»", 5),
)


class Clipper(Protocol):
    def start(self) -> None: ...

    def stop(self) -> np.ndarray: ...


@dataclass(frozen=True)
class Attempt:
    label: str
    heard: str

    @property
    def hit(self) -> bool:
        return heard_name(self.heard)


def heard_name(text: str) -> bool:
    """True if some word of the phrase starts with the stem of the name."""
    words = re.findall(r"\w+", text.lower().replace("ё", "е"))
    return any(word.startswith(WAKE_STEM) for word in words)


def record_clip(
    recorder: Clipper, seconds: float, sleep: Callable[[float], object] = time.sleep
) -> np.ndarray:
    """Record for a fixed time; the recorder is stopped even on Ctrl+C."""
    recorder.start()
    try:
        sleep(seconds)
    finally:
        audio = recorder.stop()
    return audio


def summarize(attempts: list[Attempt]) -> str:
    if not attempts:
        return "no clips"
    hits = sum(1 for a in attempts if a.hit)
    lines = [f"name found in {hits} of {len(attempts)} clips"]
    lines += [f"  missed [{a.label}]: {a.heard!r}" for a in attempts if not a.hit]
    return "\n".join(lines)


def main() -> None:
    from friday.recorder import Recorder
    from friday.stt import SpeechToText

    logging.basicConfig(level=logging.WARNING)
    stt = SpeechToText()
    print("Прогреваю распознавание речи...")
    stt.warm_up()
    recorder = Recorder()
    recorder.open()
    attempts: list[Attempt] = []
    try:
        for label, seconds in SCENARIOS:
            for number in range(1, REPEATS + 1):
                input(
                    f"\n[{number}/{REPEATS}] Enter, потом сразу говори {label} ({seconds} с): "
                )
                heard = stt.transcribe(record_clip(recorder, seconds))
                attempts.append(Attempt(label, heard))
                print(
                    f"  услышала: {heard!r}  -> {'ЕСТЬ' if attempts[-1].hit else 'НЕТ'}"
                )

        print("\n" + summarize(attempts))

        input(
            f"\nТеперь {NEGATIVE_SECONDS} с обычной речи БЕЗ имени "
            "(расскажи что-нибудь, как будто ассистента нет). Enter, потом говори: "
        )
        text = stt.transcribe(record_clip(recorder, NEGATIVE_SECONDS))
        print(f"услышала: {text!r}")
        print(f"ложное срабатывание: {'ДА' if heard_name(text) else 'нет'}")
    finally:
        recorder.close()


if __name__ == "__main__":
    main()
