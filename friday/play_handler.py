"""Glue: "play this song" phrase -> search -> start -> spoken answer.

The handler never returns None for a recognized request, even when something
breaks: otherwise the phrase would fall through to the LLM and Friday would
chat about a song instead of saying why it did not start.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.assistant import CommandReply
from friday.music_search import SearchResult, SearchStatus
from friday.play_request import parse_play_request
from friday.track_launcher import LaunchResult, LaunchStatus

logger = logging.getLogger(__name__)

Handler = Callable[[str], CommandReply | None]

_SEARCH_ANSWERS = {
    SearchStatus.NOT_FOUND: "Не нашла такой трек.",
    SearchStatus.NO_TOKEN: "Для поиска нужен токен Яндекс Музыки.",
    SearchStatus.ERROR: "Поиск сейчас не работает.",
}
_LAUNCH_ANSWERS = {
    LaunchStatus.ALREADY_PLAYING: "Этот трек уже играет.",
    LaunchStatus.NO_PANEL: "Не вижу страницу трека в Яндекс Музыке.",
    LaunchStatus.WRONG_TRACK: "Открылся другой трек, не стала включать.",
    LaunchStatus.NOT_CONFIRMED: "Нажала, но музыка не заиграла.",
    LaunchStatus.ERROR: "Не получилось запустить трек.",
}
_UNEXPECTED = "Что-то пошло не так с музыкой."


class Searcher(Protocol):
    def find(self, query: str) -> SearchResult: ...


class Launcher(Protocol):
    def launch(self, link: str, title: str) -> LaunchResult: ...


def make_play_handler(search: Searcher, launcher: Launcher) -> Handler:
    def handle(text: str) -> CommandReply | None:
        query = parse_play_request(text)
        if query is None:
            return None
        try:
            found = search.find(query)
            if found.status is not SearchStatus.FOUND or found.track is None:
                return CommandReply(
                    _SEARCH_ANSWERS.get(found.status, _UNEXPECTED), spoken=True
                )
            track = found.track
            launched = launcher.launch(track.link, track.title)
        except Exception:
            logger.exception("play request failed")
            return CommandReply(_UNEXPECTED, spoken=True)
        if launched.status is LaunchStatus.STARTED:
            return CommandReply(f"Включаю {track.display_name}", spoken=True)
        return CommandReply(
            _LAUNCH_ANSWERS.get(launched.status, _UNEXPECTED), spoken=True
        )

    return handle


def chain_handlers(*handlers: Handler) -> Handler:
    """Ask the handlers in order; the first non-None answer wins."""

    def handle(text: str) -> CommandReply | None:
        for handler in handlers:
            reply = handler(text)
            if reply is not None:
                return reply
        return None

    return handle
