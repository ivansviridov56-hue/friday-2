"""Find one Yandex Music artist for a spoken phrase.

Same rules as music_search: needs YM_TOKEN, the token is never logged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from friday.music_search import ClientFactory, SearchStatus, _default_factory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Artist:
    artist_id: str
    name: str

    @property
    def link(self) -> str:
        return f"yandexmusic://artist/{self.artist_id}"


@dataclass(frozen=True)
class ArtistResult:
    status: SearchStatus
    artist: Artist | None = None


def _to_artist(raw: Any) -> Artist | None:
    artist_id = getattr(raw, "id", None)
    name = getattr(raw, "name", None)
    if artist_id is None or not name:
        return None
    return Artist(str(artist_id), name)


class ArtistSearch:
    def __init__(
        self, token: str | None, client_factory: ClientFactory | None = None
    ) -> None:
        self._token = (token or "").strip()
        self._factory = client_factory or _default_factory
        self._client: Any = None

    def find(self, query: str) -> ArtistResult:
        query = " ".join(query.split())
        if not query:
            return ArtistResult(SearchStatus.NOT_FOUND)
        if not self._token:
            return ArtistResult(SearchStatus.NO_TOKEN)
        try:
            if self._client is None:
                self._client = self._factory(self._token)
            response = self._client.search(query, type_="artist")
        except Exception as error:
            logger.warning("artist search failed: %s", type(error).__name__)
            return ArtistResult(SearchStatus.ERROR)
        results = getattr(getattr(response, "artists", None), "results", None) or []
        for raw in results:
            artist = _to_artist(raw)
            if artist is not None:
                logger.info("artist search %r -> %s", query, artist.name)
                return ArtistResult(SearchStatus.FOUND, artist)
        return ArtistResult(SearchStatus.NOT_FOUND)
