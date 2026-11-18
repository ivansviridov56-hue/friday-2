"""Glue: "play this artist" phrase -> search -> start -> spoken answer.

Like play_handler: never returns None for a recognized request, so a failure is
spoken instead of falling through to the LLM.
"""

from __future__ import annotations

import logging
from typing import Protocol

from friday.artist_request import parse_artist_request
from friday.artist_search import ArtistResult
from friday.assistant import CommandReply
from friday.music_search import SearchStatus
from friday.play_handler import Handler, Launcher
from friday.track_launcher import LaunchStatus

logger = logging.getLogger(__name__)

_SEARCH_ANSWERS = {
    SearchStatus.NOT_FOUND: "Не нашла такого исполнителя.",
    SearchStatus.NO_TOKEN: "Для поиска нужен токен Яндекс Музыки.",
    SearchStatus.ERROR: "Поиск сейчас не работает.",
}
_LAUNCH_ANSWERS = {
    LaunchStatus.ALREADY_PLAYING: "Этот исполнитель уже играет.",
    LaunchStatus.NO_PANEL: "Не вижу страницу исполнителя в Яндекс Музыке.",
    LaunchStatus.WRONG_TRACK: "Открылась другая страница, не стала включать.",
    LaunchStatus.NOT_CONFIRMED: "Нажала, но музыка не заиграла.",
    LaunchStatus.ERROR: "Не получилось запустить исполнителя.",
}
_UNEXPECTED = "Что-то пошло не так с музыкой."


class ArtistSearcher(Protocol):
    def find(self, query: str) -> ArtistResult: ...


def make_artist_handler(search: ArtistSearcher, launcher: Launcher) -> Handler:
    def handle(text: str) -> CommandReply | None:
        query = parse_artist_request(text)
        if query is None:
            return None
        try:
            found = search.find(query)
            if found.status is not SearchStatus.FOUND or found.artist is None:
                return CommandReply(
                    _SEARCH_ANSWERS.get(found.status, _UNEXPECTED), spoken=True
                )
            artist = found.artist
            launched = launcher.launch(artist.link, artist.name)
        except Exception:
            logger.exception("artist request failed")
            return CommandReply(_UNEXPECTED, spoken=True)
        if launched.status is LaunchStatus.STARTED:
            return CommandReply(f"Включаю {artist.name}", spoken=True)
        return CommandReply(
            _LAUNCH_ANSWERS.get(launched.status, _UNEXPECTED), spoken=True
        )

    return handle
