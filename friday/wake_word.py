"""Fuzzy match of the wake word "Пятница" in a transcribed phrase.

Whisper sometimes mishears the name when it stands alone ("Ветница", "Пятенца"),
so an exact stem match is not enough. A word counts as the name when it is
similar enough to it and has a plausible length (this keeps "пятнадцать",
"пятно", "пятка" out). Pure functions, no microphone or model involved.

Two ways to ask:
- contains_wake_word: the name anywhere in the phrase (lenient, used by tests/probes);
- split_wake_phrase: the name must START the phrase (after at most two lead-in words
  like "эй" or "слушай"). This is what continuous listening uses, so that a weekday
  ("в пятницу поедем") or a song lyric does not wake the assistant.
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
_LEAD_WORDS = frozenset(
    {
        "эй",
        "слушай",
        "слушайте",
        "привет",
        "ну",
        "так",
        "ладно",
        "алло",
        "окей",
        "ок",
        "а",
    }
)
MAX_LEAD_WORDS = 2
_TRIM = " \t\n,.!?:;-—…«»\"'"


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower().replace("ё", "е"))


def _is_name(word: str, threshold: float) -> bool:
    if not _MIN_LEN <= len(word) <= _MAX_LEN:
        return False
    return SequenceMatcher(None, WAKE_WORD, word).ratio() >= threshold


def contains_wake_word(text: str, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """True if some word of the phrase is the name or a close mishearing of it."""
    for word in _words(text):
        if _is_name(word, threshold):
            log.debug("wake word matched by %r", word)
            return True
    return False


def split_wake_phrase(text: str, threshold: float = DEFAULT_THRESHOLD) -> str | None:
    """If the phrase starts with the name, return what follows it, else None.

    "Слушай, Пятница, включи музыку" -> "включи музыку"; "Пятница" -> "" (the name
    alone: the command is expected in the next phrase); "в пятницу поедем" -> None.
    """
    skipped = 0
    for match in re.finditer(r"\w+", text):
        word = match.group().lower().replace("ё", "е")
        if _is_name(word, threshold):
            log.debug("wake word matched by %r", word)
            return text[match.end() :].lstrip(_TRIM).rstrip()
        if word in _LEAD_WORDS and skipped < MAX_LEAD_WORDS:
            skipped += 1
            continue
        return None
    return None
