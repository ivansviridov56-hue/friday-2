"""Recognize music commands in a transcribed phrase.

Matches word stems, not exact phrases, because Whisper inflects and misspells
words. To avoid hijacking free conversation, most commands need a music word
("музыка", "трек", "песня", ...) and a short phrase.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class MusicCommand(Enum):
    PAUSE = "pause"
    PLAY = "play"
    NEXT = "next"
    PREVIOUS = "previous"
    NOW_PLAYING = "now_playing"


# A group matches if any of its stems matches any word. A stem starting with
# "=" must equal the whole word; any other stem matches the start of a word.
Group = tuple[str, ...]

_MUSIC = (
    "музык",
    "музик",
    "мьюзик",
    "яндекс",
    "трек",
    "песн",
    "композиц",
    "плеер",
    "воспроизвед",
)
_SONG = ("песн", "трек", "композиц")
_FILLERS = frozenset({"пятница", "пожалуйста", "давай", "ну"})


@dataclass(frozen=True)
class _Rule:
    command: MusicCommand
    alternatives: tuple[tuple[Group, ...], ...]  # any one alternative is enough
    max_words: int


_RULES = (
    _Rule(
        MusicCommand.NOW_PLAYING,
        (
            (
                ("=что", "=кто", "=какая", "=какой"),
                ("играет", "звучит", "поет", "поют"),
            ),
            (("=как",), ("называет",), _SONG),
            (("=что",), ("=за",), _SONG),
        ),
        max_words=8,
    ),
    _Rule(
        MusicCommand.NEXT,
        ((("следующ", "пропуст", "переключ", "скип"), _MUSIC),),
        max_words=6,
    ),
    _Rule(
        MusicCommand.PREVIOUS,
        ((("предыдущ", "прошл", "верни", "назад"), _MUSIC),),
        max_words=6,
    ),
    _Rule(
        MusicCommand.PAUSE,
        (
            (("пауз",),),
            (("останов", "выключ", "отключ", "заглуш", "стоп"), _MUSIC),
        ),
        max_words=6,
    ),
    _Rule(
        MusicCommand.PLAY,
        (
            (
                (
                    "включ",
                    "продолж",
                    "возобнов",
                    "запуст",
                    "играй",
                    "поставь",
                    "сыграй",
                ),
                _MUSIC,
            ),
        ),
        max_words=3,
    ),
)


def _words(text: str) -> list[str]:
    found = re.findall(r"\w+", text.lower().replace("ё", "е"))
    return [word for word in found if word not in _FILLERS]


def _has(words: list[str], group: Group) -> bool:
    for stem in group:
        for word in words:
            if stem.startswith("="):
                if word == stem[1:]:
                    return True
            elif word.startswith(stem):
                return True
    return False


def parse_music_command(text: str) -> MusicCommand | None:
    """Return the music command in the phrase, or None if it is not one."""
    words = _words(text)
    if not words:
        return None
    for rule in _RULES:
        if len(words) > rule.max_words:
            continue
        for alternative in rule.alternatives:
            if all(_has(words, group) for group in alternative):
                log.info("music command %s from %r", rule.command.name, text)
                return rule.command
    return None
