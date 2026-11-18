"""Recognize the "what is on the screen" command in a transcribed phrase.

Strict on purpose: the word "экран" is required, and the phrase must start with
"что ... на экране" or with "посмотри" / "опиши". So "выключи экран",
"что такое экран" and "запомни, что на экране ..." are not hijacked.
"""

from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

_SCREEN_STEM = "экран"
_START_VERBS = ("посмотр", "опиш")
_FILLERS = frozenset(
    {"пятница", "пожалуйста", "давай", "ну", "а", "мне", "скажи", "расскажи"}
)
_MAX_WORDS = 7


def _words(text: str) -> list[str]:
    found = re.findall(r"\w+", text.lower().replace("ё", "е"))
    return [word for word in found if word not in _FILLERS]


def is_screen_request(text: str) -> bool:
    """True if the phrase asks Friday to look at the screen and describe it."""
    words = _words(text)
    if not words or len(words) > _MAX_WORDS:
        return False
    if not any(word.startswith(_SCREEN_STEM) for word in words):
        return False
    first = words[0]
    if first == "что":
        matched = any(
            a == "на" and b.startswith(_SCREEN_STEM) for a, b in zip(words, words[1:])
        )
    else:
        matched = first.startswith(_START_VERBS)
    if matched:
        log.info("screen request from %r", text)
    return matched
