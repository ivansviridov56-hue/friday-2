import pytest

from friday.assistant import CommandReply
from friday.music_search import SearchResult, SearchStatus, Track
from friday.play_handler import chain_handlers, make_play_handler
from friday.track_launcher import LaunchResult, LaunchStatus

TRACK = Track("555328", "29639675", "Полетели", "Филипп Киркоров")


class FakeSearch:
    def __init__(self, result=None, error=None):
        self.result = result or SearchResult(SearchStatus.FOUND, TRACK)
        self.error = error
        self.queries = []

    def find(self, query):
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.result


class FakeLauncher:
    def __init__(self, status=LaunchStatus.STARTED, error=None):
        self.status = status
        self.error = error
        self.calls = []

    def launch(self, link, title):
        self.calls.append((link, title))
        if self.error:
            raise self.error
        return LaunchResult(self.status, title)


def make(search=None, launcher=None):
    search = search or FakeSearch()
    launcher = launcher or FakeLauncher()
    return make_play_handler(search, launcher), search, launcher


def test_not_a_play_request_is_ignored():
    handler, search, launcher = make()
    assert handler("как дела") is None
    assert search.queries == [] and launcher.calls == []


def test_started_is_spoken_with_track_name():
    handler, search, launcher = make()
    reply = handler("включи песню Полетели Киркоров")
    assert reply == CommandReply("Включаю Филипп Киркоров, Полетели", spoken=True)
    assert search.queries == ["Полетели Киркоров"]


def test_launch_gets_link_and_title():
    handler, _, launcher = make()
    handler("включи песню Полетели")
    assert launcher.calls == [(TRACK.link, TRACK.title)]


def test_already_playing_is_spoken():
    handler, _, _ = make(launcher=FakeLauncher(LaunchStatus.ALREADY_PLAYING))
    reply = handler("включи песню Полетели")
    assert reply is not None
    assert reply.spoken and "уже играет" in reply.text


@pytest.mark.parametrize(
    "status",
    [SearchStatus.NOT_FOUND, SearchStatus.NO_TOKEN, SearchStatus.ERROR],
)
def test_search_failures_are_spoken_and_nothing_is_launched(status):
    handler, _, launcher = make(search=FakeSearch(SearchResult(status)))
    reply = handler("включи песню Полетели")
    assert reply is not None and reply.spoken and reply.text
    assert launcher.calls == []


@pytest.mark.parametrize(
    "status",
    [
        LaunchStatus.WRONG_TRACK,
        LaunchStatus.NO_PANEL,
        LaunchStatus.NOT_CONFIRMED,
        LaunchStatus.ERROR,
    ],
)
def test_launch_failures_are_spoken(status):
    handler, _, _ = make(launcher=FakeLauncher(status))
    reply = handler("включи песню Полетели")
    assert reply is not None and reply.spoken and reply.text
    assert "Включаю" not in reply.text


def test_search_exception_gives_error_reply_not_none():
    handler, _, launcher = make(search=FakeSearch(error=RuntimeError("x")))
    reply = handler("включи песню Полетели")
    assert reply is not None and reply.spoken
    assert launcher.calls == []


def test_launcher_exception_gives_error_reply_not_none():
    handler, _, _ = make(launcher=FakeLauncher(error=RuntimeError("x")))
    reply = handler("включи песню Полетели")
    assert reply is not None and reply.spoken


def test_chain_first_answer_wins():
    first = lambda text: CommandReply("one")  # noqa: E731
    second = lambda text: CommandReply("two")  # noqa: E731
    reply = chain_handlers(first, second)("x")
    assert reply is not None and reply.text == "one"


def test_chain_falls_through_to_next():
    second = lambda text: CommandReply("two")  # noqa: E731
    reply = chain_handlers(lambda text: None, second)("x")
    assert reply is not None and reply.text == "two"


def test_chain_returns_none_when_nobody_answers():
    assert chain_handlers(lambda text: None, lambda text: None)("x") is None
