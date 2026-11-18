"""Recognize the "play My Wave" command in a transcribed phrase.

Only the plain command is matched: "my wave" (with the word "my") and, unless
the phrase is just "my wave", a play verb. Longer phrases ("... by mood",
"... for an artist") are left for later stages, so they are not hijacked here.
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


def _words(text: str) -> list[str]:
    found = re.findall(r"\w+", text.lower().replace("ё", "е"))
    return [word for word in found if word not in _FILLERS]


def _has_my_wave(words: list[str]) -> bool:
    return any(
        first in _MY and second.startswith(_WAVE_STEM)
        for first, second in zip(words, words[1:])
    )


def is_wave_request(text: str) -> bool:
    """True if the phrase asks to start the plain "My Wave"."""
    words = _words(text)
    if not _has_my_wave(words):
        return False
    if len(words) == 2:
        matched = True
    else:
        has_verb = any(word.startswith(_VERBS) for word in words)
        matched = has_verb and len(words) <= _MAX_WORDS_WITH_VERB
    if matched:
        log.info("wave request from %r", text)
    return matched
