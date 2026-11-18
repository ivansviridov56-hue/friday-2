"""Parser for memory phrases: "запомни ...", "забудь ...", "что ты обо мне помнишь".

Pure functions, no I/O. The parser is strict on purpose: a phrase must START with
the command verb (or be a short "what do you remember about me" question), so free
conversation is never hijacked and goes to the LLM as usual.

A request is returned even when its text is empty ("Запомни." / "Забудь."), so the
handler can ask what exactly to remember or forget instead of passing it to the LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from friday.memory_store import normalize


class MemoryAction(Enum):
    REMEMBER = "remember"
    FORGET = "forget"
    RECALL = "recall"


@dataclass(frozen=True)
class MemoryRequest:
    action: MemoryAction
    text: str


_SEP = r"[\W_]*"
_FLAGS = re.IGNORECASE | re.DOTALL

_REMEMBER = re.compile(
    rf"^\s*запомн(?:и|ите)\b{_SEP}(?:пожалуйста\b{_SEP})?(?:что\b(?!-){_SEP})?(.*)$",
    _FLAGS,
)
_FORGET = re.compile(rf"^\s*забуд(?:ь|ьте)\b{_SEP}(?:пожалуйста\b{_SEP})?(.*)$", _FLAGS)
_FORGET_LEAD = re.compile(
    rf"^(?:(?:о\s+том|про\s+то)[\W_]+что|про|обо|об|о|что)\b(?!-){_SEP}", _FLAGS
)

_TRIM = " \t\r\n.,;:!?…"
_RECALL_MAX_WORDS = 8
_RECALL_VERBS = {"помнишь", "знаешь"}
_RECALL_SELF = ("обо мне", "про меня")
# Never search the memory for these: "забудь всё" must not wipe facts containing "все".
_GENERIC_QUERIES = {"все", "это", "этом", "этого", "то", "того"}
_MIN_QUERY_LENGTH = 3


def parse_memory_request(text: str) -> MemoryRequest | None:
    """Return the memory request in the phrase, or None for ordinary speech."""
    match = _REMEMBER.match(text)
    if match:
        return MemoryRequest(MemoryAction.REMEMBER, _clean(match.group(1)))

    match = _FORGET.match(text)
    if match:
        rest = _FORGET_LEAD.sub("", match.group(1).strip(), count=1)
        return MemoryRequest(MemoryAction.FORGET, _forget_query(_clean(rest)))

    if _is_recall(text):
        return MemoryRequest(MemoryAction.RECALL, "")
    return None


def _clean(text: str) -> str:
    """Trim punctuation at both ends and collapse repeated spaces."""
    return " ".join(text.strip(_TRIM).split())


def _forget_query(query: str) -> str:
    key = normalize(query)
    if len(key) < _MIN_QUERY_LENGTH or key in _GENERIC_QUERIES:
        return ""
    return query


def _is_recall(text: str) -> bool:
    key = normalize(text)
    words = key.split()
    if not words or len(words) > _RECALL_MAX_WORDS:
        return False
    if not (key.startswith("что ты") or words[0] == "расскажи"):
        return False
    return bool(_RECALL_VERBS & set(words)) and any(s in key for s in _RECALL_SELF)
