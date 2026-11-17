"""Find one Yandex Music track for a spoken phrase.

Needs a token (YM_TOKEN). Without one the search reports NO_TOKEN and the rest
of the music control keeps working. The token is never logged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)

# Versions that are almost never what a person means by "play X".
UNWANTED_VERSION_STEMS = (
    "instrumental",
    "инструментал",
    "karaoke",
    "караоке",
    "minus",
    "минус",
    "acapella",
    "a cappella",
    "акапелла",
)

ClientFactory = Callable[[str], Any]


class SearchStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    NO_TOKEN = "no_token"
    ERROR = "error"


@dataclass(frozen=True)
class Track:
    track_id: str
    album_id: str
    title: str
    artists: str
    version: str | None = None

    @property
    def link(self) -> str:
        return f"yandexmusic://album/{self.album_id}/track/{self.track_id}"

    @property
    def display_name(self) -> str:
        return f"{self.artists}, {self.title}" if self.artists else self.title


@dataclass(frozen=True)
class SearchResult:
    status: SearchStatus
    track: Track | None = None


def _default_factory(token: str) -> Any:
    from yandex_music import Client

    return Client(token).init()


def _to_track(raw: Any) -> Track | None:
    """Convert a library track; None if it cannot be played from a link."""
    if getattr(raw, "available", True) is False:
        return None
    albums = getattr(raw, "albums", None) or []
    track_id = getattr(raw, "id", None)
    title = getattr(raw, "title", None)
    if not albums or albums[0].id is None or track_id is None or not title:
        return None
    names = [
        artist.name for artist in (getattr(raw, "artists", None) or []) if artist.name
    ]
    return Track(
        track_id=str(track_id),
        album_id=str(albums[0].id),
        title=title,
        artists=", ".join(names),
        version=getattr(raw, "version", None),
    )


def _is_unwanted(track: Track) -> bool:
    text = f"{track.title} {track.version or ''}".lower()
    return any(stem in text for stem in UNWANTED_VERSION_STEMS)


def pick_track(raw_tracks: Iterable[Any], query: str) -> Track | None:
    """First playable track, skipping Instrumental/Karaoke unless asked for."""
    candidates = [t for t in map(_to_track, raw_tracks) if t is not None]
    if not candidates:
        return None
    asked_for_special = any(stem in query.lower() for stem in UNWANTED_VERSION_STEMS)
    if not asked_for_special:
        for track in candidates:
            if not _is_unwanted(track):
                return track
    return candidates[0]


class TrackSearch:
    def __init__(
        self, token: str | None, client_factory: ClientFactory | None = None
    ) -> None:
        self._token = (token or "").strip()
        self._factory = client_factory or _default_factory
        self._client: Any = None

    def find(self, query: str) -> SearchResult:
        query = " ".join(query.split())
        if not query:
            return SearchResult(SearchStatus.NOT_FOUND)
        if not self._token:
            return SearchResult(SearchStatus.NO_TOKEN)
        try:
            if self._client is None:
                self._client = self._factory(self._token)
            response = self._client.search(query, type_="track")
        except Exception as error:
            # Only the type: the message of a network error could carry request details.
            logger.warning("music search failed: %s", type(error).__name__)
            return SearchResult(SearchStatus.ERROR)
        tracks = getattr(getattr(response, "tracks", None), "results", None) or []
        track = pick_track(tracks, query)
        if track is None:
            return SearchResult(SearchStatus.NOT_FOUND)
        logger.info("music search %r -> %s", query, track.display_name)
        return SearchResult(SearchStatus.FOUND, track)
