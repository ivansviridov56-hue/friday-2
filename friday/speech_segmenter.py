"""Cut a continuous audio stream into phrases by pauses (energy based).

Pure logic, no microphone and no model: feed() takes chunks of any size and
returns the phrases that have just ended. The noise floor is measured at the
start and adapts during silence, so a constantly noisy room is not mistaken
for speech. A short click is dropped, a long monologue is cut at `max_phrase_s`.
"""

from __future__ import annotations

import logging
from collections import deque

import numpy as np

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
DEFAULT_MIN_RMS = 0.004  # a quiet lavalier in a quiet room speaks at about 0.01
DEFAULT_NOISE_FACTOR = 3.0


class SpeechSegmenter:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        frame_ms: int = 30,
        min_rms: float = DEFAULT_MIN_RMS,
        noise_factor: float = DEFAULT_NOISE_FACTOR,
        start_frames: int = 3,
        end_silence_s: float = 0.8,
        min_speech_s: float = 0.3,
        max_phrase_s: float = 12.0,
        preroll_s: float = 0.3,
        calibration_s: float = 0.3,
    ) -> None:
        if sample_rate <= 0 or frame_ms <= 0:
            raise ValueError("sample_rate and frame_ms must be positive")
        if min_rms <= 0 or noise_factor < 1 or start_frames < 1:
            raise ValueError("bad detector settings")
        if (
            min(end_silence_s, min_speech_s, max_phrase_s) <= 0
            or min(preroll_s, calibration_s) < 0
        ):
            raise ValueError("bad timing settings")
        self._frame_len = sample_rate * frame_ms // 1000
        frame_s = self._frame_len / sample_rate
        self._min_rms = min_rms
        self._noise_factor = noise_factor
        self._start_frames = start_frames
        self._end_frames = max(1, round(end_silence_s / frame_s))
        self._min_speech_frames = max(1, round(min_speech_s / frame_s))
        self._max_frames = max(1, round(max_phrase_s / frame_s))
        self._pending = np.zeros(0, dtype=np.float32)
        self._recent: deque[np.ndarray] = deque(
            maxlen=round(preroll_s / frame_s) + start_frames
        )
        self._noise_floor: float | None = None
        self._calibration_frames = max(1, round(calibration_s / frame_s))
        self._calibration_rms: list[float] = []
        self._loud_run = 0
        self._frames: list[np.ndarray] | None = None  # None while idle
        self._quiet_run = 0
        self._speech_frames = 0

    @property
    def in_speech(self) -> bool:
        return self._frames is not None

    def feed(self, samples: np.ndarray) -> list[np.ndarray]:
        """Add audio; return the phrases that ended with this chunk."""
        data = np.asarray(samples, dtype=np.float32).reshape(-1)
        self._pending = np.concatenate([self._pending, data])
        phrases: list[np.ndarray] = []
        n = self._frame_len
        while self._pending.size >= n:
            frame, self._pending = self._pending[:n], self._pending[n:]
            phrase = self._on_frame(frame)
            if phrase is not None:
                phrases.append(phrase)
        return phrases

    def reset(self) -> None:
        """Forget everything heard so far (e.g. after the assistant spoke)."""
        self._pending = np.zeros(0, dtype=np.float32)
        self._recent.clear()
        self._loud_run = 0
        self._frames = None
        self._quiet_run = 0
        self._speech_frames = 0

    def _threshold(self) -> float:
        floor = self._noise_floor or 0.0
        return max(self._min_rms, floor * self._noise_factor)

    def _on_frame(self, frame: np.ndarray) -> np.ndarray | None:
        rms = float(np.sqrt(np.mean(frame * frame)))
        if self._noise_floor is None:  # the first moments only measure the background
            self._calibration_rms.append(rms)
            if len(self._calibration_rms) >= self._calibration_frames:
                self._noise_floor = float(np.mean(self._calibration_rms))
            return None
        loud = rms > self._threshold()
        if self._frames is None:
            return self._idle_frame(frame, rms, loud)
        return self._speaking_frame(frame, loud)

    def _idle_frame(self, frame: np.ndarray, rms: float, loud: bool) -> None:
        self._recent.append(frame)
        if not loud:
            self._loud_run = 0
            assert self._noise_floor is not None
            self._noise_floor = self._noise_floor * 0.95 + rms * 0.05
            return None
        self._loud_run += 1
        if self._loud_run >= self._start_frames:
            self._frames = list(self._recent)
            self._quiet_run = 0
            self._speech_frames = self._loud_run
            self._loud_run = 0
            self._recent.clear()
        return None

    def _speaking_frame(self, frame: np.ndarray, loud: bool) -> np.ndarray | None:
        assert self._frames is not None
        self._frames.append(frame)
        if loud:
            self._quiet_run = 0
            self._speech_frames += 1
        else:
            self._quiet_run += 1
        ended = self._quiet_run >= self._end_frames
        if not ended and len(self._frames) < self._max_frames:
            return None
        frames, self._frames = self._frames, None
        speech_frames, self._speech_frames = self._speech_frames, 0
        if speech_frames < self._min_speech_frames:
            log.debug("short sound dropped (%d speech frames)", speech_frames)
            return None
        return np.concatenate(frames)
