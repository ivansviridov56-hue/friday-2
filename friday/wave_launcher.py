"""Start My Wave and confirm that something really plays.

Pure logic: finding the wave player and asking "is anything playing" are
injected, so everything here is covered by tests. The UI side is in wave_ui.py.
If something already plays, nothing is pressed: the middle button would be
"Pause" at that moment.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Callable, Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class WaveStatus(Enum):
    STARTED = "started"
    ALREADY_PLAYING = "already_playing"
    NO_PLAYER = "no_player"
    NOT_CONFIRMED = "not_confirmed"
    ERROR = "error"


class WavePlayer(Protocol):
    def press_play(self) -> None: ...


class WaveLauncher:
    def __init__(
        self,
        find_player: Callable[[], WavePlayer | None],
        is_playing: Callable[[], bool],
        *,
        prepare: Callable[[], None] | None = None,
        after_start: Callable[[], None] | None = None,
        is_running: Callable[[], bool] | None = None,
        open_wave: Callable[[], None] | None = None,
        cold_start_timeout: float = 20.0,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        player_timeout: float = 5.0,
        confirm_timeout: float = 5.0,
        poll_interval: float = 0.3,
    ) -> None:
        self._find_player = find_player
        self._is_playing = is_playing
        self._prepare = prepare
        self._after_start = after_start
        self._is_running = is_running
        self._open_wave = open_wave
        self._cold_start_timeout = cold_start_timeout
        self._sleep = sleep
        self._monotonic = monotonic
        self._player_timeout = player_timeout
        self._confirm_timeout = confirm_timeout
        self._interval = poll_interval

    def launch(self) -> WaveStatus:
        if self._safe_playing():
            return WaveStatus.ALREADY_PLAYING
        self._safe_prepare()
        timeout = self._player_timeout
        if self._start_app_if_closed():
            timeout = self._cold_start_timeout
        player = self._poll(self._safe_player, timeout, lambda v: v is not None)
        if player is None:
            logger.info("wave player not found")
            return WaveStatus.NO_PLAYER
        try:
            player.press_play()
        except Exception as error:
            logger.warning("pressing play failed: %s", type(error).__name__)
            return WaveStatus.ERROR
        if self._poll(self._safe_playing, self._confirm_timeout, bool):
            self._safe_after_start()
            return WaveStatus.STARTED
        logger.info("play was pressed but the session does not report playback")
        return WaveStatus.NOT_CONFIRMED

    def _safe_player(self) -> WavePlayer | None:
        try:
            return self._find_player()
        except Exception as error:
            logger.debug("player lookup failed: %s", type(error).__name__)
            return None

    def _safe_after_start(self) -> None:
        if self._after_start is None:
            return
        try:
            self._after_start()
        except Exception as error:
            logger.debug("after_start failed: %s", type(error).__name__)

    def _safe_prepare(self) -> None:
        if self._prepare is None:
            return
        try:
            self._prepare()
        except Exception as error:
            logger.debug("prepare failed: %s", type(error).__name__)

    def _start_app_if_closed(self) -> bool:
        """Open the wave link only when Yandex Music is not running at all."""
        if self._is_running is None or self._open_wave is None:
            return False
        try:
            if self._is_running():
                return False
        except Exception as error:
            logger.debug("running check failed: %s", type(error).__name__)
            return False
        try:
            self._open_wave()
        except Exception as error:
            logger.warning("opening the wave link failed: %s", type(error).__name__)
            return False
        logger.info("Yandex Music is closed: opened the wave link")
        return True

    def _safe_playing(self) -> bool:
        try:
            return bool(self._is_playing())
        except Exception as error:
            logger.debug("playback check failed: %s", type(error).__name__)
            return False

    def _poll(
        self, check: Callable[[], T], timeout: float, ok: Callable[[T], bool]
    ) -> T | None:
        deadline = self._monotonic() + timeout
        while True:
            value = check()
            if ok(value):
                return value
            if self._monotonic() >= deadline:
                return None
            self._sleep(self._interval)
