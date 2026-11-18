from types import SimpleNamespace as NS

from friday.artist_search import ArtistSearch
from friday.music_search import SearchStatus


def raw(artist_id, name):
    return NS(id=artist_id, name=name)


class FakeClient:
    def __init__(self, results=None, error=None):
        self.results = results
        self.error = error
        self.calls = []

    def search(self, text, type_=None):
        self.calls.append((text, type_))
        if self.error:
            raise self.error
        return NS(artists=NS(results=self.results))


def make(client, token="t"):
    created = []

    def factory(tok):
        created.append(tok)
        return client

    return ArtistSearch(token, factory), created


def test_found_artist_has_name_and_link():
    search, _ = make(FakeClient([raw(167049, "Филипп Киркоров")]))
    result = search.find("Киркорова")
    assert result.status is SearchStatus.FOUND
    assert result.artist is not None
    assert result.artist.name == "Филипп Киркоров"
    assert result.artist.link == "yandexmusic://artist/167049"


def test_no_token():
    search, created = make(FakeClient([raw(1, "A")]), token="")
    assert search.find("A").status is SearchStatus.NO_TOKEN
    assert created == []


def test_empty_query_is_not_found():
    search, created = make(FakeClient([raw(1, "A")]))
    assert search.find("   ").status is SearchStatus.NOT_FOUND
    assert created == []


def test_no_results():
    search, _ = make(FakeClient(None))
    assert search.find("A").status is SearchStatus.NOT_FOUND


def test_exception_gives_error():
    search, _ = make(FakeClient(error=RuntimeError("x")))
    assert search.find("A").status is SearchStatus.ERROR


def test_client_is_created_once():
    client = FakeClient([raw(1, "A")])
    search, created = make(client)
    search.find("A")
    search.find("B")
    assert len(created) == 1
    assert len(client.calls) == 2


def test_unusable_results_are_skipped():
    search, _ = make(FakeClient([raw(None, "A"), raw(5, None), raw(7, "B")]))
    result = search.find("B")
    assert result.artist is not None and result.artist.name == "B"
