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
# "=" must equal the whole word; a stem starting with "?" matches the start of a
# word whatever its first letter is (a smeared first sound, "йграет" for "играет");
# any other stem matches the start of a word.
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

# How a quiet voice over music is written: "што играет", "стойграет" (see _match_glued).
_ALIASES: dict[str, str] = {"што": "что", "шо": "что", "чо": "что", "сто": "что"}
GLUED_MIN = 7  # a single unknown word this long may be two words without a space
GLUED_MAX = 20


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
                ("?играет", "играют", "звучит", "поет", "поют"),
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
    return [_ALIASES[w] if w in _ALIASES else w for w in found if w not in _FILLERS]


def _has(words: list[str], group: Group) -> bool:
    for stem in group:
        for word in words:
            if stem.startswith("="):
                if word == stem[1:]:
                    return True
            elif stem.startswith("?"):
                body = stem[2:]  # the stem without "?" and without its first letter
                if len(word) > len(body) and word[1 : 1 + len(body)] == body:
                    return True
            elif word.startswith(stem):
                return True
            elif word.startswith(stem):
                return True
    return False


def _match(words: list[str]) -> MusicCommand | None:
    for rule in _RULES:
        if len(words) > rule.max_words:
            continue
        for alternative in rule.alternatives:
            if all(_has(words, group) for group in alternative):
                return rule.command
    return None


def _match_glued(word: str) -> MusicCommand | None:
    """A quiet voice over music can come out as one word: "стойграет" is "что играет".

    Only for a phrase of a single word: try to cut it into two words.
    """
    if not GLUED_MIN <= len(word) <= GLUED_MAX:
        return None
    for cut in range(2, len(word) - 1):
        parts = [_ALIASES.get(part, part) for part in (word[:cut], word[cut:])]
        command = _match(parts)
        if command is not None:
            return command
    return None


def parse_music_command(text: str) -> MusicCommand | None:
    """Return the music command in the phrase, or None if it is not one."""
    words = _words(text)
    if not words:
        return None
    command = _match(words)
    if command is None and len(words) == 1:
        command = _match_glued(words[0])
    if command is not None:
        log.info("music command %s from %r", command.name, text)
    return command
