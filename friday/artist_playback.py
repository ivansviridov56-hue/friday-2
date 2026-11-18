"""Ask the Yandex Music media session whether a given artist is playing now."""

from __future__ import annotations

import asyncio
from typing import Callable

from friday.music import YM_APP_IDS, PlaybackStatus, SessionLister
from friday.track_launcher import normalize


async def _check(list_sessions: SessionLister, name: str) -> bool:
    wanted = normalize(name)
    if not wanted:
        return False
    for session in await list_sessions():
        if session.app_id.lower().strip() not in YM_APP_IDS:
            continue
        info = await session.now_playing()
        return info.status is PlaybackStatus.PLAYING and wanted in normalize(
            info.artist
        )
    return False


def make_is_artist_playing(list_sessions: SessionLister) -> Callable[[str], bool]:
    """Return a sync check for TrackLauncher (runs in a worker thread)."""

    def is_playing(name: str) -> bool:
        return asyncio.run(_check(list_sessions, name))

    return is_playing
