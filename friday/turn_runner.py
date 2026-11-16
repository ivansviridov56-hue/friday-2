"""Runs one voice turn at a time in a background thread.

While a turn is in progress, new audio is dropped (first version: no queue,
no interruption).
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

import numpy as np

log = logging.getLogger(__name__)

Spawn = Callable[[Callable[[], None]], None]


def _spawn_thread(task: Callable[[], None]) -> None:
    threading.Thread(target=task, name="voice-turn", daemon=True).start()


class TurnRunner:
    def __init__(
        self,
        handler: Callable[[np.ndarray], object],
        spawn: Spawn = _spawn_thread,
    ) -> None:
        self._handler = handler
        self._spawn = spawn
        self._busy = False
        self._lock = threading.Lock()

    @property
    def is_busy(self) -> bool:
        return self._busy

    def submit(self, audio: np.ndarray) -> bool:
        """Start a turn. Returns False if the audio was dropped."""
        with self._lock:
            if self._busy:
                log.info("busy answering, phrase ignored")
                return False
            self._busy = True
        try:
            self._spawn(lambda: self._run(audio))
        except Exception:
            log.exception("could not start the turn")
            self._finish()
            return False
        return True

    def _run(self, audio: np.ndarray) -> None:
        try:
            self._handler(audio)
        except Exception:
            log.exception("turn failed")
        finally:
            self._finish()

    def _finish(self) -> None:
        with self._lock:
            self._busy = False
