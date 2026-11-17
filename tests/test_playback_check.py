import asyncio

import pytest

from friday.music import NowPlaying, PlaybackStatus
from friday.playback_check import make_is_playing


class FakeSession:
    def __init__(self, app_id: str, title: str, status: PlaybackStatus) -> None:
        self.app_id = app_id
        self._info = NowPlaying(title=title, artist="A", status=status)

    async def now_playing(self) -> NowPlaying:
        return self._info


def checker(*sessions):
    async def list_sessions():
        return list(sessions)

    return make_is_playing(list_sessions)


YM = "ru.yandex.desktop.music"


def test_playing_same_title():
    assert checker(FakeSession(YM, "Song", PlaybackStatus.PLAYING))("Song")


def test_title_match_ignores_case_and_yo():
    assert checker(FakeSession(YM, "ЁЛКА", PlaybackStatus.PLAYING))("елка")


@pytest.mark.parametrize("status", [PlaybackStatus.PAUSED, PlaybackStatus.OTHER])
def test_not_playing_status(status):
    assert not checker(FakeSession(YM, "Song", status))("Song")


def test_other_title_is_not_a_match():
    assert not checker(FakeSession(YM, "Other", PlaybackStatus.PLAYING))("Song")


def test_other_apps_are_ignored():
    chrome = FakeSession("chrome", "Song", PlaybackStatus.PLAYING)
    assert not checker(chrome)("Song")


def test_no_sessions():
    assert not checker()("Song")
