"""Recognize the "play My Wave" commands in a transcribed phrase.

Two commands are matched. The plain one: "my wave" (with the word "my") and,
unless the phrase is just "my wave", a play verb. And the mood one: the same
plus exactly one mood word ("calm", "cheerful", "energetic", "sad"). Other long
phrases ("... for an artist", "... for a workout") are left alone, so they are
not hijacked here.
"""

from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

_VERBS = ("включ", "запуст", "играй", "поставь")
_MY = frozenset({"моя", "мою", "моей", "мое"})
_WAVE_STEM = "волн"
_FILLERS = frozenset({"пятница", "пожалуйста", "давай", "ну"})
_MAX_WORDS_WITH_VERB = 4
_MAX_WORDS_WITH_MOOD = 6
# Yandex Music mood keys (the API names) and the word stems that mean them.
_MOOD_STEMS = (
    ("active", "бодр"),
    ("fun", "весел"),
    ("calm", "спокойн"),
    ("sad", "грустн"),
)


def _words(text: str) -> list[str]:
    found = re.findall(r"\w+", text.lower().replace("ё", "е"))
    return [word for word in found if word not in _FILLERS]


def _has_my_wave(words: list[str]) -> bool:
    return any(
        first in _MY and second.startswith(_WAVE_STEM)
        for first, second in zip(words, words[1:])
    )


def _has_my_wave_loose(words: list[str]) -> bool:
    """ "my wave" with up to one word between: "мою грустную волну"."""
    return any(
        word in _MY
        and any(other.startswith(_WAVE_STEM) for other in words[index + 1 : index + 3])
        for index, word in enumerate(words)
    )


def _moods_in(words: list[str]) -> set[str]:
    return {key for word in words for key, stem in _MOOD_STEMS if word.startswith(stem)}


def is_wave_request(text: str) -> bool:
    """True if the phrase asks to start the plain "My Wave"."""
    words = _words(text)
    if not _has_my_wave(words):
        return False
    if _moods_in(words):
        return False
    if len(words) == 2:
        matched = True
    else:
        has_verb = any(word.startswith(_VERBS) for word in words)
        matched = has_verb and len(words) <= _MAX_WORDS_WITH_VERB
    if matched:
        log.info("wave request from %r", text)
    return matched


def parse_wave_mood(text: str) -> str | None:
    """The mood key ("active", "fun", "calm", "sad") of a "My Wave by mood" request.

    None unless the phrase has "my wave", a play verb and exactly one mood.
    """
    words = _words(text)
    if len(words) > _MAX_WORDS_WITH_MOOD or not _has_my_wave_loose(words):
        return None
    if not any(word.startswith(_VERBS) for word in words):
        return None
    moods = _moods_in(words)
    if len(moods) != 1:
        return None
    mood = next(iter(moods))
    log.info("wave mood request %r from %r", mood, text)
    return mood
