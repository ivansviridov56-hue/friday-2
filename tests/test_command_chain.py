"""Tests for the voice command chain builder."""

from __future__ import annotations

import pytest

from friday.play_handler import Handler
from friday.assistant import CommandReply
from friday.command_chain import COMMAND_ORDER, build_command_chain


def _silent(_text: str) -> None:
    return None


def _all_silent() -> dict:
    return {name: _silent for name in COMMAND_ORDER}


def test_command_order_has_every_handler() -> None:
    assert COMMAND_ORDER == (
        "memory",
        "screen",
        "wave_mood",
        "wave",
        "play",
        "artist",
        "music",
    )


def test_missing_handler_raises() -> None:
    handlers = _all_silent()
    del handlers["wave"]
    with pytest.raises(ValueError, match="wave"):
        build_command_chain(handlers)


def test_unknown_handler_raises() -> None:
    handlers = _all_silent()
    handlers["weather"] = _silent
    with pytest.raises(ValueError, match="weather"):
        build_command_chain(handlers)


def test_returns_none_when_nobody_answers() -> None:
    chain = build_command_chain(_all_silent())
    assert chain("привет") is None


def test_first_in_order_wins() -> None:
    early = CommandReply("early", spoken=True)
    late = CommandReply("late", spoken=True)
    handlers = _all_silent()
    handlers["music"] = lambda _t: late
    handlers["memory"] = lambda _t: early
    chain = build_command_chain(handlers)
    assert chain("любая фраза") is early


def test_handlers_are_asked_in_order() -> None:
    asked: list[str] = []

    def spy(name: str):
        def handle(_text: str) -> None:
            asked.append(name)
            return None

        return handle

    chain = build_command_chain({name: spy(name) for name in COMMAND_ORDER})
    chain("фраза")
    assert asked == list(COMMAND_ORDER)


def test_answer_stops_the_chain() -> None:
    asked: list[str] = []
    reply = CommandReply("ok", spoken=True)

    def silent(name: str):
        def handle(_text: str) -> None:
            asked.append(name)
            return None

        return handle

    handlers: dict[str, Handler] = {name: silent(name) for name in COMMAND_ORDER}

    def wave(_text: str) -> CommandReply:
        asked.append("wave")
        return reply

    handlers["wave"] = wave
    chain = build_command_chain(handlers)
    assert chain("включи мою волну") is reply
    assert asked == ["memory", "screen", "wave_mood", "wave"]


def test_wave_mood_is_asked_before_plain_wave() -> None:
    assert COMMAND_ORDER.index("wave_mood") < COMMAND_ORDER.index("wave")
