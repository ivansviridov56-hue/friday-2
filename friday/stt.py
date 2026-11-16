"""Speech-to-text on top of faster-whisper."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

import numpy as np

from friday.cuda_dlls import add_cuda_dll_dirs

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000

ModelFactory = Callable[[str, str, str], Any]


def _default_factory(name: str, device: str, compute_type: str) -> Any:
    add_cuda_dll_dirs()
    from faster_whisper import WhisperModel

    return WhisperModel(name, device=device, compute_type=compute_type)


class SpeechToText:
    """Lazy-loaded Whisper model. Input: mono float32 audio at 16 kHz."""

    def __init__(
        self,
        model_name: str = "large-v3-turbo",
        language: str = "ru",
        device: str = "cuda",
        compute_type: str = "float16",
        model_factory: ModelFactory | None = None,
    ) -> None:
        self._model_name = model_name
        self._language = language
        self._device = device
        self._compute_type = compute_type
        self._factory = model_factory or _default_factory
        self._model: Any = None
        self._lock = threading.Lock()
        self._ready = threading.Event()

    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()

    def _get_model(self) -> Any:
        with self._lock:
            if self._model is None:
                log.info("loading STT model %s", self._model_name)
                self._model = self._factory(
                    self._model_name, self._device, self._compute_type
                )
            return self._model

    def warm_up(self) -> None:
        """Load the model and run once on silence (the first run is slow)."""
        silence = np.zeros(SAMPLE_RATE * 3, dtype=np.float32)
        segments, _ = self._get_model().transcribe(silence, language=self._language)
        list(segments)
        self._ready.set()
        log.info("STT model is warm")

    def warm_up_async(self) -> threading.Thread:
        thread = threading.Thread(target=self.warm_up, name="stt-warmup", daemon=True)
        thread.start()
        return thread

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        samples = np.asarray(audio, dtype=np.float32)
        segments, _ = self._get_model().transcribe(
            samples, language=self._language, vad_filter=True
        )
        parts = (s.text.strip() for s in segments)
        return " ".join(p for p in parts if p)
