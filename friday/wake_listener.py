"""Continuous listening for the wake word "Пятница".

Audio frames come from the microphone subscription (Recorder.add_listener) into a
queue; a worker thread cuts them into phrases (SpeechSegmenter), recognizes each
phrase and checks that it STARTS with the name. The text after the name goes to
`submit` as a ready command. If only the name was said, the next phrase (within
`command_wait_s`) is the command. The listener is deaf while the assistant is busy
or the push-to-talk button is held (`is_busy`), and for a moment afterwards, so it
never hears the assistant's own voice.

Phrase texts are NOT written to the log unless `log_text` is on (everything said
near the microphone is recognized here): the log only has lengths and timings.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable
from typing import Protocol

import numpy as np

from friday.speech_segmenter import SAMPLE_RATE, SpeechSegmenter
from friday.wake_word import split_wake_phrase

log = logging.getLogger(__name__)

COMMAND_WAIT_S = 6.0
COOLDOWN_S = 1.0
QUEUE_FRAMES = 2000


class Microphone(Protocol):
    def add_listener(self, listener: Callable[[np.ndarray], object]) -> None: ...

    def remove_listener(self, listener: Callable[[np.ndarray], object]) -> None: ...


class Transcriber(Protocol):
    def transcribe(self, audio: np.ndarray) -> str: ...


class PhraseCutter(Protocol):
    @property
    def in_speech(self) -> bool: ...

    def feed(self, samples: np.ndarray) -> list[np.ndarray]: ...

    def reset(self) -> None: ...


class WakeListener:
    def __init__(
        self,
        microphone: Microphone,
        stt: Transcriber,
        submit: Callable[[str], bool],
        is_busy: Callable[[], bool],
        *,
        segmenter: PhraseCutter | None = None,
        command_wait_s: float = COMMAND_WAIT_S,
        cooldown_s: float = COOLDOWN_S,
        on_event: Callable[[str], object] | None = None,
        log_text: bool = False,
        queue_frames: int = QUEUE_FRAMES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._microphone = microphone
        self._stt = stt
        self._submit = submit
        self._is_busy = is_busy
        self._segmenter: PhraseCutter = segmenter or SpeechSegmenter()
        self._command_wait_s = command_wait_s
        self._cooldown_s = cooldown_s
        self._on_event = on_event
        self._log_text = log_text
        self._clock = clock
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=queue_frames)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._quiet_until = 0.0
        self._waiting_until: float | None = None
        self._dropped = 0

    # -- thread plumbing -------------------------------------------------

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._microphone.add_listener(self._enqueue)
        self._thread = threading.Thread(
            target=self._run, name="wake-listener", daemon=True
        )
        self._thread.start()
        log.info("wake listener started")

    def stop(self) -> None:
        thread, self._thread = self._thread, None
        if thread is None:
            return
        self._microphone.remove_listener(self._enqueue)
        self._stop.set()
        thread.join(timeout=3)
        log.info("wake listener stopped")

    def _enqueue(self, frame: np.ndarray) -> None:
        """Called from the audio thread: only queue the frame, never block."""
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            self._dropped += 1
            if self._dropped == 1 or self._dropped % 100 == 0:
                log.warning("wake listener is behind, %d frames dropped", self._dropped)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.process(frame)
            except Exception:  # one bad frame must not stop the listening
                log.exception("wake listener failed on a frame")

    # -- logic (synchronous, tested directly) ------------------------------

    def process(self, frame: np.ndarray) -> None:
        now = self._clock()
        if self._is_busy():
            self._close_gate(now)
            return
        if now < self._quiet_until:
            self._segmenter.reset()
            return
        self._expire_wait(now)
        for phrase in self._segmenter.feed(frame):
            self._on_phrase(phrase)

    def _close_gate(self, now: float) -> None:
        self._segmenter.reset()
        self._quiet_until = now + self._cooldown_s
        if self._waiting_until is not None:
            self._waiting_until = None
            self._emit("cancel")  # someone else (the assistant, X2) owns the window now

    def _expire_wait(self, now: float) -> None:
        if (
            self._waiting_until is not None
            and now > self._waiting_until
            and not self._segmenter.in_speech
        ):
            self._waiting_until = None
            self._emit("timeout")

    def _on_phrase(self, audio: np.ndarray) -> None:
        seconds = audio.size / SAMPLE_RATE
        started = self._clock() - seconds  # when the phrase began, roughly
        waiting = self._waiting_until is not None and started <= self._waiting_until
        began = self._clock()
        try:
            text = self._stt.transcribe(audio).strip()
        except Exception:
            log.exception("wake listener: recognition failed")
            return
        rest = split_wake_phrase(text)
        self._log_phrase(seconds, self._clock() - began, rest, waiting, text)
        if waiting:
            command = text if rest is None else rest
            if command:
                self._waiting_until = None
                self._send(command)
            elif rest == "":  # the name again: keep waiting from now
                self._arm_wait()
            return  # empty text: noise, keep waiting
        if rest is None:
            return
        if rest:
            self._send(rest)
        else:
            self._arm_wait()

    def _arm_wait(self) -> None:
        self._waiting_until = self._clock() + self._command_wait_s
        self._emit("wake")

    def _send(self, command: str) -> None:
        try:
            accepted = self._submit(command)
        except Exception:
            log.exception("wake listener: submit failed")
            return
        if accepted:
            self._emit("command")
        else:
            log.info("wake listener: command dropped (assistant busy)")

    def _emit(self, name: str) -> None:
        log.info("wake listener event: %s", name)
        if self._on_event is None:
            return
        try:
            self._on_event(name)
        except Exception:
            log.exception("wake listener: event handler failed")

    def _log_phrase(
        self, seconds: float, took: float, rest: str | None, waiting: bool, text: str
    ) -> None:
        shown = f" heard={text!r}" if self._log_text else ""
        log.info(
            "wake listener: phrase %.1f s, recognized in %d ms, name=%s, waiting=%s%s%s",
            seconds,
            took * 1000,
            rest is not None,
            waiting,
            self._end_note(),
            shown,
        )

    def _end_note(self) -> str:
        """How the segmenter closed the phrase: ended=max means it was cut at the limit."""
        info = getattr(self._segmenter, "last_end", None)  # older cutters have none
        if info is None:
            return ""
        return f" ended={info.reason} floor={info.floor:.4f} thr={info.threshold:.4f}"
