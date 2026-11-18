"""Recognize "play this song" phrases and extract the search query.

Deliberately strict: a play verb first, then a song word (песня / трек /
композиция), then the query. "включи свет" or "поставь будильник" are not
play requests, so free conversation is not hijacked.
"""

from __future__ import annotations

import re

_VERBS = ("включ", "постав", "играй", "сыграй", "запуст", "воспроизвед")
_SONG_WORDS = ("песн", "трек", "композиц")
_SKIP = frozenset({"пятница", "пожалуйста", "давай", "ну", "мне", "нам", "еще"})
_MAX_GAP = 2
_MAX_QUERY_WORDS = 8
_EDGE_CHARS = " .,!?;:-—«»\"'"


def parse_play_request(text: str) -> str | None:
    """Return the track query from the phrase, or None if it is not a request."""
    words = []
    for match in re.finditer(r"\w+", text):
        word = match.group().lower().replace("ё", "е")
        if word not in _SKIP:
            words.append((word, match.end()))
    if not words or not words[0][0].startswith(_VERBS):
        return None
    last = min(len(words), 2 + _MAX_GAP)
    for word, end in words[1:last]:
        if word.startswith(_SONG_WORDS):
            query = text[end:].strip(_EDGE_CHARS)
            if not query or len(re.findall(r"\w+", query)) > _MAX_QUERY_WORDS:
                return None
            return query
    return None
