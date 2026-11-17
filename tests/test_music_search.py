import logging
from types import SimpleNamespace

import pytest

from friday.music_search import SearchStatus, TrackSearch


def raw(
    track_id: int,
    title: str = "Song",
    artists: tuple[str | None, ...] = ("Artist",),
    album_id: int | None = 7,
    version: str | None = None,
    available: bool = True,
):
    return SimpleNamespace(
        id=track_id,
        title=title,
        version=version,
        available=available,
        artists=[SimpleNamespace(name=name) for name in artists],
        albums=[SimpleNamespace(id=album_id)] if album_id is not None else [],
    )


def response(*tracks):
    return SimpleNamespace(tracks=SimpleNamespace(results=list(tracks)))


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.queries = []

    def search(self, text, type_=None):
        self.queries.append((text, type_))
        if self.error:
            raise self.error
        return self.result


def make_search(client, token="tok"):
    created = []

    def factory(value):
        created.append(value)
        return client

    return TrackSearch(token, factory), created


def found(search: TrackSearch, query: str):
    result = search.find(query)
    assert result.status is SearchStatus.FOUND
    assert result.track is not None
    return result.track


def test_picks_first_playable_track():
    search, _ = make_search(FakeClient(response(raw(1), raw(2))))
    track = found(search, "song")
    assert track.track_id == "1"
    assert track.album_id == "7"


def test_skips_instrumental_version():
    tracks = response(
        raw(1, "Till I Collapse", version="Instrumental"),
        raw(2, "Till I Collapse", version="from the film"),
    )
    search, _ = make_search(FakeClient(tracks))
    assert found(search, "till i collapse").track_id == "2"


def test_falls_back_when_only_unwanted_versions_exist():
    search, _ = make_search(FakeClient(response(raw(1, "Song", version="Karaoke"))))
    assert found(search, "song").track_id == "1"


@pytest.mark.parametrize(
    "query", ["song instrumental", "song karaoke", "песня инструментал"]
)
def test_keeps_unwanted_version_when_asked(query):
    tracks = response(raw(1, "Song", version="Instrumental"), raw(2, "Song"))
    search, _ = make_search(FakeClient(tracks))
    assert found(search, query).track_id == "1"


def test_skips_unavailable_track():
    tracks = response(raw(1, available=False), raw(2))
    search, _ = make_search(FakeClient(tracks))
    assert found(search, "song").track_id == "2"


def test_skips_track_without_album():
    tracks = response(raw(1, album_id=None), raw(2))
    search, _ = make_search(FakeClient(tracks))
    assert found(search, "song").track_id == "2"


def test_artist_without_name_is_ignored():
    search, _ = make_search(FakeClient(response(raw(1, artists=(None, "Real")))))
    assert found(search, "song").artists == "Real"


def test_link_and_display_name():
    search, _ = make_search(
        FakeClient(response(raw(5, "Title", artists=("A", "B"), album_id=9)))
    )
    track = found(search, "title")
    assert track.link == "yandexmusic://album/9/track/5"
    assert track.display_name == "A, B, Title"


@pytest.mark.parametrize("token", ["", None])
def test_no_token_means_no_client_and_no_search(token):
    client = FakeClient(response(raw(1)))
    search, created = make_search(client, token=token)
    assert search.find("song").status is SearchStatus.NO_TOKEN
    assert created == []
    assert client.queries == []


def test_empty_query_is_not_searched():
    client = FakeClient(response(raw(1)))
    search, created = make_search(client)
    assert search.find("   ").status is SearchStatus.NOT_FOUND
    assert created == []


@pytest.mark.parametrize(
    "empty_result",
    [
        None,
        SimpleNamespace(tracks=None),
        SimpleNamespace(tracks=SimpleNamespace(results=None)),
    ],
)
def test_nothing_found(empty_result):
    search, _ = make_search(FakeClient(empty_result))
    assert search.find("song").status is SearchStatus.NOT_FOUND


def test_client_creation_error_is_reported_and_next_call_retries():
    attempts = []

    def factory(token):
        attempts.append(token)
        if len(attempts) == 1:
            raise RuntimeError("network down")
        return FakeClient(response(raw(1)))

    search = TrackSearch("tok", factory)
    assert search.find("song").status is SearchStatus.ERROR
    assert search.find("song").status is SearchStatus.FOUND


def test_search_error_is_reported():
    search, _ = make_search(FakeClient(error=RuntimeError("boom")))
    assert search.find("song").status is SearchStatus.ERROR


def test_client_is_created_once():
    search, created = make_search(FakeClient(response(raw(1))))
    search.find("one")
    search.find("two")
    assert created == ["tok"]


def test_token_is_never_logged(caplog):
    def factory(token):
        raise RuntimeError(f"rejected {token}")

    search = TrackSearch("secret-token", factory)
    with caplog.at_level(logging.DEBUG):
        search.find("song")
    assert "secret-token" not in caplog.text


def test_query_whitespace_is_normalised():
    client = FakeClient(response(raw(1)))
    search, _ = make_search(client)
    search.find("  one   two ")
    assert client.queries == [("one two", "track")]
