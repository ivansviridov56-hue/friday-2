"""Ask the Yandex Music media session whether a given track is playing now."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

from friday.music import YM_APP_IDS, PlaybackStatus, SessionLister
from friday.track_launcher import normalize

logger = logging.getLogger(__name__)


async def _check(list_sessions: SessionLister, title: str) -> bool:
    for session in await list_sessions():
        if session.app_id.lower().strip() not in YM_APP_IDS:
            continue
        info = await session.now_playing()
        return info.status is PlaybackStatus.PLAYING and normalize(
            info.title
        ) == normalize(title)
    return False


def make_is_playing(list_sessions: SessionLister) -> Callable[[str], bool]:
    """Return a sync check for TrackLauncher (runs in a worker thread)."""

    def is_playing(title: str) -> bool:
        return asyncio.run(_check(list_sessions, title))

    return is_playing


async def _check_any(list_sessions: SessionLister) -> bool:
    for session in await list_sessions():
        if session.app_id.lower().strip() not in YM_APP_IDS:
            continue
        info = await session.now_playing()
        return info.status is PlaybackStatus.PLAYING
    return False


def make_is_any_playing(list_sessions: SessionLister) -> Callable[[], bool]:
    """Return a sync check: is anything playing in Yandex Music right now?"""

    def is_playing() -> bool:
        return asyncio.run(_check_any(list_sessions))

    return is_playing
