import pytest

from friday.artist_handler import make_artist_handler
from friday.artist_search import Artist, ArtistResult
from friday.assistant import CommandReply
from friday.music_search import SearchResult, SearchStatus
from friday.play_handler import chain_handlers, make_play_handler
from friday.track_launcher import LaunchResult, LaunchStatus

ARTIST = Artist("167049", "Филипп Киркоров")


class FakeSearch:
    def __init__(self, result=None, error=None):
        self.result = result or ArtistResult(SearchStatus.FOUND, ARTIST)
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
    return make_artist_handler(search, launcher), search, launcher


def test_not_a_request_is_ignored():
    handler, search, launcher = make()
    assert handler("как дела") is None
    assert search.queries == [] and launcher.calls == []


def test_started_is_spoken_with_artist_name():
    handler, search, _ = make()
    reply = handler("включи исполнителя Киркорова")
    assert reply == CommandReply("Включаю Филипп Киркоров", spoken=True)
    assert search.queries == ["Киркорова"]


def test_launch_gets_link_and_name():
    handler, _, launcher = make()
    handler("включи исполнителя Киркорова")
    assert launcher.calls == [(ARTIST.link, ARTIST.name)]


def test_already_playing_is_spoken():
    handler, _, _ = make(launcher=FakeLauncher(LaunchStatus.ALREADY_PLAYING))
    reply = handler("включи исполнителя Киркорова")
    assert reply is not None
    assert reply.spoken and "уже играет" in reply.text


@pytest.mark.parametrize(
    "status",
    [SearchStatus.NOT_FOUND, SearchStatus.NO_TOKEN, SearchStatus.ERROR],
)
def test_search_failures_are_spoken_and_nothing_is_launched(status):
    handler, _, launcher = make(search=FakeSearch(ArtistResult(status)))
    reply = handler("включи исполнителя Киркорова")
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
    reply = handler("включи исполнителя Киркорова")
    assert reply is not None and reply.spoken and reply.text
    assert "Включаю" not in reply.text


def test_search_exception_gives_error_reply_not_none():
    handler, _, launcher = make(search=FakeSearch(error=RuntimeError("x")))
    reply = handler("включи исполнителя Киркорова")
    assert reply is not None and reply.spoken
    assert launcher.calls == []


def test_launcher_exception_gives_error_reply_not_none():
    handler, _, _ = make(launcher=FakeLauncher(error=RuntimeError("x")))
    reply = handler("включи исполнителя Киркорова")
    assert reply is not None and reply.spoken


class TrackSearchSpy:
    def __init__(self):
        self.queries = []

    def find(self, query):
        self.queries.append(query)
        return SearchResult(SearchStatus.NOT_FOUND)


def test_song_of_a_group_goes_to_the_track_handler_first():
    track_search = TrackSearchSpy()
    artist_handler, artist_search, _ = make()
    handler = chain_handlers(
        make_play_handler(track_search, FakeLauncher()), artist_handler
    )
    reply = handler("включи песню группы Ленинград")
    assert reply is not None
    assert track_search.queries == ["группы Ленинград"]
    assert artist_search.queries == []
