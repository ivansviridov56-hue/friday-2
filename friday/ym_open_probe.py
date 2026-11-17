"""Probe: can a Yandex Music track be started from a link, with no UI clicks?

Copy a track link from the app (like https://music.yandex.ru/album/123/track/456), then:
    python -m friday.ym_open_probe "<link>"

Opens it through the yandexmusic:// protocol and prints what the media session
says right after opening and after a "play" command.
Live-checked tool, no unit tests (like ym_probe.py).
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

from friday.music import YM_APP_IDS
from friday.smtc import SmtcSession, list_sessions

LINK = re.compile(r"/album/(\d+)/track/(\d+)|/track/(\d+)")


def to_uri(link: str) -> str | None:
    match = LINK.search(link)
    if match is None:
        return None
    album, track, solo = match.groups()
    if solo:
        return f"yandexmusic://track/{solo}"
    return f"yandexmusic://album/{album}/track/{track}"


async def find_music() -> SmtcSession | None:
    for session in await list_sessions():
        if session.app_id.lower().strip() in YM_APP_IDS:
            return session
    return None


async def describe() -> str:
    session = await find_music()
    if session is None:
        return "Yandex Music session not found"
    info = await session.now_playing()
    return f"{info.artist} - {info.title} [{info.status.value}]"


async def main(link: str) -> None:
    uri = to_uri(link)
    if uri is None:
        print("No track id found in the link")
        return
    print("before:    ", await describe())
    print("opening:   ", uri)
    os.startfile(uri)
    await asyncio.sleep(4)
    print("after open:", await describe())
    session = await find_music()
    if session is not None:
        print("play command:", await session.play())
    await asyncio.sleep(2)
    print("after play:", await describe())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: python -m friday.ym_open_probe "<track link>"')
    else:
        asyncio.run(main(sys.argv[1]))
