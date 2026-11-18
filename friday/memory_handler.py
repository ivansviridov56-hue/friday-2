"""Glue: memory phrase -> memory store -> spoken answer.

Like the music handlers, it never returns None for a recognized request, even
when the store breaks: otherwise the phrase would fall through to the LLM and
Friday would chat about it instead of saying what happened.

Fact texts are personal data: they are spoken and shown in the window, but
never written to the log.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.assistant import CommandReply
from friday.memory_request import MemoryAction, MemoryRequest, parse_memory_request
from friday.memory_store import AddStatus

logger = logging.getLogger(__name__)

Handler = Callable[[str], CommandReply | None]

_MAX_SPOKEN_FACTS = 5
_MAX_LISTED_FORGOTTEN = 3

_ADD_ANSWERS = {
    AddStatus.ADDED: "Запомнила.",
    AddStatus.DUPLICATE: "Это я уже знаю.",
    AddStatus.EMPTY: "Что именно запомнить?",
    AddStatus.TOO_LONG: "Слишком длинно, скажи покороче.",
    AddStatus.FULL: "Память заполнена. Сначала попроси что-нибудь забыть.",
}
_ASK_REMEMBER = "Что именно запомнить?"
_ASK_FORGET = "Что именно забыть?"
_NOTHING_FOUND = "Не нашла такого в памяти."
_NOTHING_STORED = "Пока ничего о тебе не помню."
_FORGOT_MANY = "Забыла несколько фактов."
_UNEXPECTED = "Что-то пошло не так с памятью."


class Store(Protocol):
    def add(self, text: str) -> AddStatus: ...

    def forget(self, query: str) -> list[str]: ...

    def facts(self) -> list[str]: ...


def make_memory_handler(store: Store) -> Handler:
    def handle(text: str) -> CommandReply | None:
        request = parse_memory_request(text)
        if request is None:
            return None
        try:
            answer = _answer(store, request)
        except Exception:
            logger.exception("memory request failed")
            answer = _UNEXPECTED
        return CommandReply(answer, spoken=True)

    return handle


def _answer(store: Store, request: MemoryRequest) -> str:
    if request.action is MemoryAction.REMEMBER:
        if not request.text:
            return _ASK_REMEMBER
        return _ADD_ANSWERS.get(store.add(request.text), _UNEXPECTED)
    if request.action is MemoryAction.FORGET:
        if not request.text:
            return _ASK_FORGET
        return _forgot(store.forget(request.text))
    return _recalled(store.facts())


def _forgot(removed: list[str]) -> str:
    if not removed:
        return _NOTHING_FOUND
    if len(removed) > _MAX_LISTED_FORGOTTEN:
        return _FORGOT_MANY
    return "Забыла: " + "; ".join(removed)


def _recalled(facts: list[str]) -> str:
    if not facts:
        return _NOTHING_STORED
    answer = "Я помню: " + "; ".join(facts[:_MAX_SPOKEN_FACTS]) + "."
    extra = len(facts) - _MAX_SPOKEN_FACTS
    if extra > 0:
        answer += f" И ещё {extra}."
    return answer
