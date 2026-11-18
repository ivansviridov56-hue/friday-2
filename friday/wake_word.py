"""Fuzzy match of the wake word "Пятница" in a transcribed phrase.

Whisper sometimes mishears the name when it stands alone ("Ветница", "Пятенца"),
so an exact stem match is not enough. A word counts as the name when it is
similar enough to it and has a plausible length (this keeps "пятнадцать",
"пятно", "пятка" out). Pure function, no microphone or model involved.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

log = logging.getLogger(__name__)

WAKE_WORD = "пятница"
DEFAULT_THRESHOLD = 0.7
_MIN_LEN = 5
_MAX_LEN = 9


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower().replace("ё", "е"))


def contains_wake_word(text: str, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """True if some word of the phrase is the name or a close mishearing of it."""
    for word in _words(text):
        if not _MIN_LEN <= len(word) <= _MAX_LEN:
            continue
        if SequenceMatcher(None, WAKE_WORD, word).ratio() >= threshold:
            log.debug("wake word matched by %r", word)
            return True
    return False
