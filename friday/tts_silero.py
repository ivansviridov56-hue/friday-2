"""Local Russian voice: Silero TTS v5_ru, runs on the CPU without a network."""

from __future__ import annotations

import io
import logging
import struct
import threading
import time
import wave
from collections.abc import Callable, Iterable
from typing import Any

log = logging.getLogger(__name__)

MODEL_LANGUAGE = "ru"
MODEL_ID = "v5_ru"
DEFAULT_SPEAKER = "kseniya"
DEFAULT_SAMPLE_RATE = 48000
CPU_THREADS = 4
WARM_UP_TEXT = "Прогрев."


class SileroError(Exception):
    pass


def samples_to_wav(samples: Iterable[float], sample_rate: int) -> bytes:
    """Float samples in [-1, 1] -> mono 16-bit WAV bytes."""
    values = [int(max(-1.0, min(1.0, float(s))) * 32767) for s in samples]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(struct.pack(f"<{len(values)}h", *values))
    return buffer.getvalue()


def _load_model() -> Any:
    """Download (first run only) and load the model on the CPU."""
    import torch
    from silero import silero_tts

    result = silero_tts(language=MODEL_LANGUAGE, speaker=MODEL_ID)
    model = result[0]
    model.to(torch.device("cpu"))
    torch.set_num_threads(CPU_THREADS)
    return model


class SileroVoice:
    """One phrase in, WAV bytes out. The model is loaded lazily, once."""

    def __init__(
        self,
        speaker: str = DEFAULT_SPEAKER,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        loader: Callable[[], Any] | None = None,
    ) -> None:
        self._speaker = speaker
        self._sample_rate = sample_rate
        self._loader = loader or _load_model
        self._model: Any = None
        self._load_lock = threading.Lock()
        self._run_lock = threading.Lock()

    def _get_model(self) -> Any:
        with self._load_lock:
            if self._model is None:
                started = time.perf_counter()
                try:
                    model = self._loader()
                except Exception as exc:
                    raise SileroError(
                        f"cannot load the Silero model: {type(exc).__name__}"
                    ) from exc
                log.info("silero model loaded in %.1f s", time.perf_counter() - started)
                self._model = model
            return self._model

    def warm_up(self) -> None:
        """Load the model and run one short phrase (the first run is slower)."""
        model = self._get_model()
        try:
            with self._run_lock:
                model.apply_tts(
                    text=WARM_UP_TEXT,
                    speaker=self._speaker,
                    sample_rate=self._sample_rate,
                )
        except Exception as exc:
            log.warning("silero warm-up failed: %s", type(exc).__name__)

    def synthesize(self, text: str) -> bytes:
        text = text.strip()
        if not text:
            raise SileroError("empty text")
        model = self._get_model()
        started = time.perf_counter()
        try:
            with self._run_lock:
                audio = model.apply_tts(
                    text=text,
                    speaker=self._speaker,
                    sample_rate=self._sample_rate,
                )
            samples = audio.tolist()
        except Exception as exc:
            raise SileroError(f"synthesis failed: {type(exc).__name__}") from exc
        log.info(
            "silero synthesized %d chars in %d ms",
            len(text),
            int((time.perf_counter() - started) * 1000),
        )
        return samples_to_wav(samples, self._sample_rate)
