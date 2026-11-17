"""Probe: does Windows (SMTC) see Yandex Music, and can we control its own session?

Start Yandex Music and play a track, then:
    python -m friday.ym_probe             # list media sessions
    python -m friday.ym_probe --commands  # also pause / play / next on the Yandex Music session

Live-checked tool, no unit tests (like window.py).
"""

from __future__ import annotations

import asyncio
import sys

try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as Manager,
    )
except ImportError:
    Manager = None

YM_IDS = ("ru.yandex.desktop.music", "yandexmusic")


async def describe(session) -> str:
    app_id = session.source_app_user_model_id
    props = await session.try_get_media_properties_async()
    status = str(session.get_playback_info().playback_status).split(".")[-1]
    return f"{app_id!r}: {props.artist} - {props.title} [{status}]"


async def main(run_commands: bool) -> None:
    if Manager is None:
        print("No SMTC backend found. Try: pip install winsdk")
        return
    manager = await Manager.request_async()
    sessions = list(manager.get_sessions() or [])
    print(f"backend: winsdk, sessions: {len(sessions)}")
    ym = None
    for session in sessions:
        print(" -", await describe(session))
        if (session.source_app_user_model_id or "").lower().strip() in YM_IDS:
            ym = session
    if ym is None:
        print("Yandex Music session NOT found")
        return
    print("Yandex Music session found")
    if not run_commands:
        return
    steps = (
        ("pause", ym.try_pause_async),
        ("play", ym.try_play_async),
        ("next", ym.try_skip_next_async),
    )
    for name, call in steps:
        print(f"{name}: {await call()}")
        await asyncio.sleep(2)
        print("   now:", await describe(ym))


if __name__ == "__main__":
    asyncio.run(main("--commands" in sys.argv))
