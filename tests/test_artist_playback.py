from friday.artist_playback import make_is_artist_playing
from friday.music import YM_APP_IDS, NowPlaying, PlaybackStatus

YM = sorted(YM_APP_IDS)[0]


class FakeSession:
    def __init__(self, app_id: str, artist: str, status: PlaybackStatus) -> None:
        self.app_id = app_id
        self._info = NowPlaying(title="T", artist=artist, status=status)

    async def now_playing(self) -> NowPlaying:
        return self._info


def checker(*sessions):
    async def list_sessions():
        return list(sessions)

    return make_is_artist_playing(list_sessions)


def test_playing_artist_matches():
    session = FakeSession(YM, "Филипп Киркоров", PlaybackStatus.PLAYING)
    assert checker(session)("Филипп Киркоров")


def test_artist_among_several():
    session = FakeSession(YM, "ANNA ASTI, Филипп Киркоров", PlaybackStatus.PLAYING)
    assert checker(session)("Филипп Киркоров")


def test_other_artist_is_not_a_match():
    session = FakeSession(YM, "Eminem", PlaybackStatus.PLAYING)
    assert not checker(session)("Филипп Киркоров")


def test_paused_is_not_playing():
    session = FakeSession(YM, "Eminem", PlaybackStatus.PAUSED)
    assert not checker(session)("Eminem")


def test_other_apps_are_ignored():
    chrome = FakeSession("chrome", "Eminem", PlaybackStatus.PLAYING)
    assert not checker(chrome)("Eminem")


def test_no_sessions():
    assert not checker()("Eminem")


def test_case_and_yo_are_ignored():
    session = FakeSession(YM, "ЁЛКА", PlaybackStatus.PLAYING)
    assert checker(session)("елка")
