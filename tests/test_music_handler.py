import pytest

from friday.music import (
    ERROR,
    NO_ANSWER,
    NOT_FOUND,
    PAUSED,
    RESUMED,
    SKIPPED,
    WENT_BACK,
)
from friday.music_handler import make_music_handler


class FakeMusic:
    def __init__(self, answer="ответ"):
        self.answer = answer
        self.calls = []

    def _do(self, name):
        self.calls.append(name)
        return self.answer

    def play(self):
        return self._do("play")

    def pause(self):
        return self._do("pause")

    def skip_next(self):
        return self._do("skip_next")

    def skip_previous(self):
        return self._do("skip_previous")

    def now_playing(self):
        return self._do("now_playing")


@pytest.mark.parametrize(
    "text, call",
    [
        ("пауза", "pause"),
        ("включи музыку", "play"),
        ("следующий трек", "skip_next"),
        ("предыдущий трек", "skip_previous"),
        ("что играет", "now_playing"),
    ],
)
def test_command_calls_the_matching_method_and_returns_its_text(text, call):
    music = FakeMusic("ответ")
    reply = make_music_handler(music)(text)
    assert reply is not None
    assert reply.text == "ответ"
    assert music.calls == [call]


@pytest.mark.parametrize(
    "text, phrase",
    [
        ("пауза", PAUSED),
        ("включи музыку", RESUMED),
        ("следующий трек", SKIPPED),
        ("предыдущий трек", WENT_BACK),
    ],
)
def test_success_confirmations_are_not_spoken(text, phrase):
    reply = make_music_handler(FakeMusic(phrase))(text)
    assert reply is not None
    assert reply.text == phrase
    assert reply.spoken is False


@pytest.mark.parametrize("phrase", [NOT_FOUND, NO_ANSWER, ERROR])
def test_errors_are_spoken(phrase):
    reply = make_music_handler(FakeMusic(phrase))("пауза")
    assert reply is not None
    assert reply.spoken is True


def test_now_playing_is_spoken():
    reply = make_music_handler(FakeMusic("Сейчас играет Нигатив."))("что играет")
    assert reply is not None
    assert reply.spoken is True


def test_ordinary_speech_returns_none_and_touches_nothing():
    music = FakeMusic()
    assert make_music_handler(music)("привет, как дела") is None
    assert music.calls == []


def test_empty_phrase_returns_none():
    assert make_music_handler(FakeMusic())("") is None
