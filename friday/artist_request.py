"""Recognize "play this artist" phrases and extract the search query.

Strict like play_request: a play verb first, then an artist word (исполнитель /
артист / группа ...), then the name. "включи свет" is not a request.
"""

from __future__ import annotations

import re

_VERBS = ("включ", "постав", "играй", "сыграй", "запуст", "воспроизвед")
_MARKS = ("исполнител", "артист", "певец", "певц", "певиц", "групп")
_SKIP = frozenset({"пятница", "пожалуйста", "давай", "ну", "мне", "нам", "еще"})
_MAX_GAP = 1
_MAX_QUERY_WORDS = 5
_EDGE_CHARS = " .,!?;:-—«»\"'"


def parse_artist_request(text: str) -> str | None:
    """Return the artist query from the phrase, or None if it is not a request."""
    words = []
    for match in re.finditer(r"\w+", text):
        word = match.group().lower().replace("ё", "е")
        if word not in _SKIP:
            words.append((word, match.end()))
    if not words or not words[0][0].startswith(_VERBS):
        return None
    last = min(len(words), 2 + _MAX_GAP)
    for word, end in words[1:last]:
        if word.startswith(_MARKS):
            query = text[end:].strip(_EDGE_CHARS)
            if not query or len(re.findall(r"\w+", query)) > _MAX_QUERY_WORDS:
                return None
            return query
    return None
