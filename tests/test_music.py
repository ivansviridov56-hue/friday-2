import pytest

from friday.music import (
    ERROR,
    NO_ANSWER,
    NOT_FOUND,
    NOTHING_PLAYING,
    PAUSED,
    RESUMED,
    SKIPPED,
    WENT_BACK,
    MusicController,
    NowPlaying,
    PlaybackStatus,
)

PLAYING = NowPlaying("Некрасивая красота", "Нигатив", PlaybackStatus.PLAYING)


class FakeSession:
    def __init__(self, app_id, now=PLAYING, accepted=True, error=None):
        self.app_id = app_id
        self.calls = []
        self._now = now
        self._accepted = accepted
        self._error = error

    async def _do(self, name):
        self.calls.append(name)
        if self._error:
            raise self._error
        return self._accepted

    async def play(self):
        return await self._do("play")

    async def pause(self):
        return await self._do("pause")

    async def skip_next(self):
        return await self._do("skip_next")

    async def skip_previous(self):
        return await self._do("skip_previous")

    async def now_playing(self):
        if self._error:
            raise self._error
        return self._now


def controller(*sessions):
    async def lister():
        return list(sessions)

    return MusicController(lister)


def test_command_goes_only_to_the_music_session():
    music = FakeSession("ru.yandex.desktop.music")
    browser = FakeSession("Yandex")
    assert controller(browser, music).pause() == PAUSED
    assert music.calls == ["pause"]
    assert browser.calls == []


def test_app_id_match_ignores_case_and_spaces():
    music = FakeSession("  RU.Yandex.Desktop.Music ")
    assert controller(music).play() == RESUMED
    assert music.calls == ["play"]


def test_browser_only_means_music_not_found_and_browser_untouched():
    browser = FakeSession("Yandex")
    assert controller(browser).pause() == NOT_FOUND
    assert browser.calls == []


@pytest.mark.parametrize(
    "name, phrase",
    [
        ("play", RESUMED),
        ("pause", PAUSED),
        ("skip_next", SKIPPED),
        ("skip_previous", WENT_BACK),
    ],
)
def test_each_command_calls_the_right_method_and_says_its_phrase(name, phrase):
    music = FakeSession("yandexmusic")
    assert getattr(controller(music), name)() == phrase
    assert music.calls == [name]


def test_refused_command_says_no_answer():
    music = FakeSession("yandexmusic", accepted=False)
    assert controller(music).skip_next() == NO_ANSWER


def test_listing_error_is_spoken_not_raised():
    async def broken():
        raise RuntimeError("no winsdk")

    assert MusicController(broken).pause() == ERROR


def test_session_error_is_spoken_not_raised():
    music = FakeSession("yandexmusic", error=RuntimeError("boom"))
    assert controller(music).pause() == ERROR


def test_now_playing_while_playing():
    music = FakeSession("yandexmusic")
    assert (
        controller(music).now_playing() == "Сейчас играет Нигатив, Некрасивая красота."
    )


def test_now_playing_while_paused():
    paused = NowPlaying("Некрасивая красота", "Нигатив", PlaybackStatus.PAUSED)
    music = FakeSession("yandexmusic", now=paused)
    assert controller(music).now_playing() == "На паузе: Нигатив, Некрасивая красота."


def test_now_playing_without_title():
    empty = NowPlaying("", "", PlaybackStatus.OTHER)
    music = FakeSession("yandexmusic", now=empty)
    assert controller(music).now_playing() == NOTHING_PLAYING
