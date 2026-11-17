"""Control Yandex Music through its own Windows media session.

Not global media keys: a command goes only to the Yandex Music session, so a
browser tab or another player is never touched. The Windows-specific part
lives in friday/smtc.py; this module only knows the MediaSession protocol.

Live check: python -m friday.music now|play|pause|next|prev
"""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

log = logging.getLogger(__name__)

YM_APP_IDS = ("ru.yandex.desktop.music", "yandexmusic")

PAUSED = "Поставила на паузу."
RESUMED = "Продолжаю."
SKIPPED = "Включаю следующий."
WENT_BACK = "Возвращаюсь к предыдущему."
NOT_FOUND = "Не вижу Яндекс Музыку. Запусти её и включи любой трек."
NO_ANSWER = "Музыка не ответила на команду."
ERROR = "Не получилось связаться с Яндекс Музыкой."
NOTHING_PLAYING = "Не понимаю, что сейчас играет."


class PlaybackStatus(Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    OTHER = "other"


@dataclass(frozen=True)
class NowPlaying:
    title: str
    artist: str
    status: PlaybackStatus


class MediaSession(Protocol):
    @property
    def app_id(self) -> str: ...

    async def now_playing(self) -> NowPlaying: ...
    async def play(self) -> bool: ...
    async def pause(self) -> bool: ...
    async def skip_next(self) -> bool: ...
    async def skip_previous(self) -> bool: ...


SessionLister = Callable[[], Awaitable[Sequence[MediaSession]]]


def _sentence(text: str) -> str:
    """Add a final period unless the text already ends with punctuation."""
    return text if text.endswith((".", "!", "?", "…")) else text + "."


class MusicController:
    """Sync facade: every method returns a phrase the assistant can speak."""

    def __init__(self, list_sessions: SessionLister) -> None:
        self._list_sessions = list_sessions

    def play(self) -> str:
        return self._run(self._send("play", RESUMED))

    def pause(self) -> str:
        return self._run(self._send("pause", PAUSED))

    def skip_next(self) -> str:
        return self._run(self._send("skip_next", SKIPPED))

    def skip_previous(self) -> str:
        return self._run(self._send("skip_previous", WENT_BACK))

    def now_playing(self) -> str:
        return self._run(self._describe())

    @staticmethod
    def _run(coro: Coroutine[Any, Any, str]) -> str:
        try:
            return asyncio.run(coro)
        except Exception:
            log.exception("music command failed")
            return ERROR

    async def _find(self) -> MediaSession | None:
        sessions = await self._list_sessions()
        for session in sessions:
            if session.app_id.lower().strip() in YM_APP_IDS:
                return session
        log.warning(
            "Yandex Music session not found, app ids: %s",
            [s.app_id for s in sessions],
        )
        return None

    async def _send(self, name: str, done: str) -> str:
        session = await self._find()
        if session is None:
            return NOT_FOUND
        accepted = await getattr(session, name)()
        return done if accepted else NO_ANSWER

    async def _describe(self) -> str:
        session = await self._find()
        if session is None:
            return NOT_FOUND
        info = await session.now_playing()
        if not info.title:
            return NOTHING_PLAYING
        who = f"{info.artist}, {info.title}" if info.artist else info.title
        if info.status is PlaybackStatus.PAUSED:
            return f"На паузе: {_sentence(who)}"
        return f"Сейчас играет {_sentence(who)}"


def main(argv: list[str] | None = None) -> None:
    from friday.smtc import list_sessions

    logging.basicConfig(level=logging.INFO)
    controller = MusicController(list_sessions)
    actions = {
        "now": controller.now_playing,
        "play": controller.play,
        "pause": controller.pause,
        "next": controller.skip_next,
        "prev": controller.skip_previous,
    }
    args = sys.argv[1:] if argv is None else argv
    name = args[0] if args else ""
    if name not in actions:
        print("usage: python -m friday.music now|play|pause|next|prev")
        return
    print(actions[name]())


if __name__ == "__main__":
    main()
