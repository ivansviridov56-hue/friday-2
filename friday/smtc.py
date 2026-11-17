"""Windows media sessions (SMTC) adapter. Live-checked, no unit tests.

The only module that imports winsdk. Everything else uses the MediaSession
protocol from friday.music.
"""

from __future__ import annotations

from friday.music import NowPlaying, PlaybackStatus

try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as Manager,
    )
except ImportError:
    Manager = None

# Values seen in the live probe: 4 = playing, 5 = paused.
_STATUS = {4: PlaybackStatus.PLAYING, 5: PlaybackStatus.PAUSED}


class SmtcSession:
    def __init__(self, raw) -> None:
        self._raw = raw

    @property
    def app_id(self) -> str:
        return self._raw.source_app_user_model_id or ""

    async def now_playing(self) -> NowPlaying:
        props = await self._raw.try_get_media_properties_async()
        code = int(self._raw.get_playback_info().playback_status)
        return NowPlaying(
            title=props.title or "",
            artist=props.artist or "",
            status=_STATUS.get(code, PlaybackStatus.OTHER),
        )

    async def play(self) -> bool:
        return bool(await self._raw.try_play_async())

    async def pause(self) -> bool:
        return bool(await self._raw.try_pause_async())

    async def skip_next(self) -> bool:
        return bool(await self._raw.try_skip_next_async())

    async def skip_previous(self) -> bool:
        return bool(await self._raw.try_skip_previous_async())


async def list_sessions() -> list[SmtcSession]:
    if Manager is None:
        raise RuntimeError("winsdk is not installed (pip install winsdk)")
    manager = await Manager.request_async()
    raw_sessions = manager.get_sessions()
    if raw_sessions is None:
        return []
    return [SmtcSession(raw) for raw in raw_sessions]
