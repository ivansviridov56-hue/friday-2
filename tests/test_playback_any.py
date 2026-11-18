import asyncio
from types import SimpleNamespace

from friday.music import PlaybackStatus
from friday.playback_check import make_is_any_playing


class FakeSession:
    def __init__(self, app_id: str, status) -> None:
        self.app_id = app_id
        self._status = status

    async def now_playing(self):
        return SimpleNamespace(status=self._status, title="x")


def _lister(*sessions):
    async def list_sessions():
        return list(sessions)

    return list_sessions


def test_true_when_yandex_music_is_playing() -> None:
    session = FakeSession("yandexmusic", PlaybackStatus.PLAYING)
    assert make_is_any_playing(_lister(session))() is True


def test_false_when_yandex_music_is_not_playing() -> None:
    session = FakeSession("yandexmusic", "other")
    assert make_is_any_playing(_lister(session))() is False


def test_other_apps_and_no_sessions_are_ignored() -> None:
    other = FakeSession("chrome", PlaybackStatus.PLAYING)
    assert make_is_any_playing(_lister(other))() is False
    assert make_is_any_playing(_lister())() is False
