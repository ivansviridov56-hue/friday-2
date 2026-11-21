"""Reads the Yandex Music media session for the cover circle. Live-checked, no unit tests."""

from __future__ import annotations

import asyncio

from friday.music import YM_APP_IDS
from friday.smtc import SmtcSession, list_sessions


async def _find() -> SmtcSession | None:
    for session in await list_sessions():
        if session.app_id.lower().strip() in YM_APP_IDS:
            return session
    return None


async def _key() -> tuple[str, str] | None:
    session = await _find()
    if session is None:
        return None
    info = await session.now_playing()
    if not info.title:
        return None
    return (info.title, info.artist)


async def _cover() -> bytes | None:
    session = await _find()
    if session is None:
        return None
    return await session.thumbnail_bytes()


class SmtcCoverSource:
    def key(self) -> tuple[str, str] | None:
        return asyncio.run(_key())

    def cover(self) -> bytes | None:
        return asyncio.run(_cover())
