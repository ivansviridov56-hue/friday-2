"""Probe: how Silero TTS sounds and how fast it is on this machine.

Live-checked diagnostic, no unit tests. Writes wav files to a temp folder
(never into the repo) and opens that folder.
"""

from __future__ import annotations

import os
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import torch
from silero import silero_tts

SAMPLE_RATE = 48000
SPEAKERS = ("aidar", "baya", "kseniya", "xenia", "eugene")
TEXT = (
    "Сейчас играет ROCKET, Инкассатор. "
    "Я рада, что ты доволен. Чем могу быть полезна?"
)


def _save(path: Path, audio: torch.Tensor) -> float:
    samples = (audio.numpy() * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(samples.tobytes())
    return len(samples) / SAMPLE_RATE


def main() -> None:
    folder = Path(tempfile.mkdtemp(prefix="silero_probe_"))
    start = time.perf_counter()
    model = silero_tts(language="ru", speaker="v5_ru")[0]
    print(f"model loaded in {time.perf_counter() - start:.1f} s")
    model.to(torch.device("cpu"))
    torch.set_num_threads(4)
    model.apply_tts(text="Прогрев.", speaker="xenia", sample_rate=SAMPLE_RATE)
    for speaker in SPEAKERS:
        start = time.perf_counter()
        audio = model.apply_tts(text=TEXT, speaker=speaker, sample_rate=SAMPLE_RATE)
        took = time.perf_counter() - start
        seconds = _save(folder / f"{speaker}.wav", audio)
        print(f"{speaker}: {took * 1000:.0f} ms for {seconds:.1f} s of audio")
    print(f"files: {folder}")
    os.startfile(folder)  # type: ignore[attr-defined]  # Windows only


if __name__ == "__main__":
    main()
