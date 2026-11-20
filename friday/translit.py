"""Turn Latin words into Cyrillic so the Russian Silero voice can read them."""

from __future__ import annotations

import re

_LATIN_WORD = re.compile(r"[A-Za-z]+")

# Common names and words with a hand-picked spelling (keys are lowercase).
_DICTIONARY = {
    "yandex": "яндекс",
    "music": "мьюзик",
    "python": "пайтон",
    "github": "гитхаб",
    "windows": "виндоус",
    "youtube": "ютуб",
}

# Longer pairs first, so "sh" wins over "s" + "h".
_DIGRAPHS = {
    "sh": "ш",
    "ch": "ч",
    "zh": "ж",
    "kh": "х",
    "ph": "ф",
    "ts": "ц",
    "ck": "к",
}

_LETTERS = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "дж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
}


def _spell(word: str) -> str:
    """Letter-by-letter fallback for a lowercase Latin word."""
    result: list[str] = []
    i = 0
    while i < len(word):
        pair = word[i : i + 2]
        if pair in _DIGRAPHS:
            result.append(_DIGRAPHS[pair])
            i += 2
        else:
            result.append(_LETTERS[word[i]])
            i += 1
    return "".join(result)


def _apply_case(original: str, cyrillic: str) -> str:
    if len(original) > 1 and original.isupper():
        return cyrillic.upper()
    if original[0].isupper():
        return cyrillic.capitalize()
    return cyrillic


def _convert_word(match: re.Match[str]) -> str:
    original = match.group(0)
    lower = original.lower()
    cyrillic = _DICTIONARY.get(lower) or _spell(lower)
    return _apply_case(original, cyrillic)


def latin_to_cyrillic(text: str) -> str:
    """Replace every Latin word in the text; everything else stays as it is."""
    return _LATIN_WORD.sub(_convert_word, text)
