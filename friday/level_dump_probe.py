"""Probe for stage 11c-5: record loudness numbers of a real room with music.

Run: python -m friday.level_dump_probe
Close the assistant first (it holds the microphone). The script walks you through
a short scenario and writes ONE NUMBER PER 30 ms FRAME (RMS loudness) plus step
marks to data/probes/. No sound and no words are saved. The numbers are enough to
replay the speech segmenter offline exactly as it ran live.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from friday.mic_level_probe import FRAME_MS, Listenable, frame_levels
from friday.speech_segmenter import SAMPLE_RATE

log = logging.getLogger(__name__)

HEADER = "# friday level dump v1"


@dataclass(frozen=True)
class Step:
    label: str  # one word, goes to the file
    instruction: str  # shown to the user
    seconds: float


@dataclass(frozen=True)
class Mark:
    time_s: float
    label: str


SCENARIO = [
    Step("music_only", "Музыка играет, ты молчишь.", 15),
    Step(
        "say_then_pause",
        "Скажи «Пятница, что играет» и сразу поставь музыку на ПАУЗУ вручную.",
        8,
    ),
    Step("quiet_after_pause", "Музыка на паузе. Молчи.", 12),
    Step("say_in_quiet", "Скажи «Пятница, пауза» (в тишине).", 8),
    Step("quiet_end", "Молчи.", 5),
]


def format_dump(levels: np.ndarray, marks: list[Mark], frame_ms: int) -> str:
    if levels.size == 0:
        raise ValueError("no levels to write")
    lines = [HEADER, f"# frame_ms={frame_ms}"]
    for mark in marks:
        if not mark.label or any(ch.isspace() for ch in mark.label):
            raise ValueError("a mark label must be one word")
        lines.append(f"# mark {mark.time_s:.3f} {mark.label}")
    lines.extend(f"{float(v):.6f}" for v in levels)
    return "\n".join(lines) + "\n"


def parse_dump(text: str) -> tuple[np.ndarray, list[Mark], int]:
    lines = text.splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError("not a level dump")
    frame_ms = FRAME_MS
    marks: list[Mark] = []
    values: list[float] = []
    for line in lines[1:]:
        if line.startswith("# frame_ms="):
            frame_ms = int(line.split("=", 1)[1])
        elif line.startswith("# mark "):
            _, _, when, label = line.split(" ", 3)
            marks.append(Mark(float(when), label))
        elif line and not line.startswith("#"):
            values.append(float(line))
    if not values:
        raise ValueError("no levels in the dump")
    return np.array(values, dtype=np.float32), marks, frame_ms


def record_steps(
    recorder: Listenable,
    steps: list[Step],
    sleep: Callable[[float], object] = time.sleep,
    say: Callable[[str], object] = print,
) -> tuple[np.ndarray, list[Mark]]:
    """Record the whole scenario; marks are placed by the amount of audio heard."""
    chunks: list[np.ndarray] = []
    marks: list[Mark] = []
    listener = chunks.append
    recorder.add_listener(listener)
    try:
        for step in steps:
            heard = sum(c.size for c in chunks)
            marks.append(Mark(round(heard / SAMPLE_RATE, 3), step.label))
            say(step.instruction)
            sleep(step.seconds)
    finally:
        recorder.remove_listener(listener)
    audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    return audio, marks


def default_output_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return root / "data" / "probes" / f"levels_{stamp}.txt"


def main() -> None:
    from friday.recorder import Recorder

    logging.basicConfig(level=logging.WARNING)
    recorder = Recorder()
    recorder.open()
    try:
        input("Включи свою музыку как обычно, как при работе. Enter, чтобы начать: ")
        audio, marks = record_steps(recorder, SCENARIO)
    finally:
        recorder.close()
    levels = frame_levels(audio)
    if levels.size == 0:
        print("Звук не пришёл.")
        return
    path = default_output_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_dump(levels, marks, FRAME_MS), encoding="utf-8")
    print(f"\nГотово: {path} ({levels.size} кадров). Пришли этот файл.")


if __name__ == "__main__":
    main()
