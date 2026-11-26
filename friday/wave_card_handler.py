"""Glue: "play the wave <title>" phrase -> start the card -> spoken answer.

Like the other handlers, it never returns None for a recognized request, even
when something breaks: otherwise the phrase would fall through to the LLM.
A phrase without a card title returns None and goes on down the chain.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.assistant import CommandReply
from friday.wave_card_launcher import CardResult, CardStatus
from friday.wave_cards import parse_wave_card_request
from friday.wave_request import is_wave_request

logger = logging.getLogger(__name__)

Handler = Callable[[str], CommandReply | None]

_ANSWERS = {
    CardStatus.NO_WINDOW: "Не вижу окно Яндекс Музыки.",
    CardStatus.NO_CARDS: "Не вижу карточки волн. Открой Мою волну в приложении.",
    CardStatus.NO_MATCH: "Не нашла такую волну среди карточек.",
    CardStatus.NOT_CONFIRMED: "Нажала, но волна не заиграла.",
}
_FALLBACK = "Не получилось включить эту волну."

# Nothing was pressed in these cases, so the plain My Wave may still take over.
_NOTHING_PRESSED = (CardStatus.NO_WINDOW, CardStatus.NO_CARDS, CardStatus.NO_MATCH)


class CardStarter(Protocol):
    def launch(self, query: str) -> CardResult: ...


def _answer(result: CardResult) -> str:
    if result.status is CardStatus.STARTED and result.title:
        return f"Включаю волну: {result.title}."
    return _ANSWERS.get(result.status, _FALLBACK)


def make_wave_card_handler(launcher: CardStarter) -> Handler:
    def handle(text: str) -> CommandReply | None:
        query = parse_wave_card_request(text)
        if query is None:
            return None
        try:
            result = launcher.launch(query)
        except Exception:
            logger.exception("wave card request failed")
            return CommandReply(_FALLBACK, spoken=True)
        if result.status in _NOTHING_PRESSED and is_wave_request(text):
            return None  # e.g. "включи мою волну снова": no such card
        return CommandReply(_answer(result), spoken=True)

    return handle
