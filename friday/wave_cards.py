"""Pick a My Wave card by a spoken title.

Pure logic, no UI: the card names come from the Yandex Music window (found
in a later step). A card name looks like "Моя волна по жанру Украинский рок";
the part after the kind marker is the title a person would say. Cards that
are not waves ("Сингл ...", "Настроить Мою волну", the page panel "Моя волна")
are dropped. Ties go to the shorter title, then to the card listed first.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable

log = logging.getLogger(__name__)

WAVE_PREFIX = "моя волна"
MAX_REQUEST_WORDS = 8
EXACT_TITLE_BONUS = 10

_KINDS = (
    ("по жанру", "genre"),
    ("под занятие", "activity"),
    ("по характеру", "character"),
    ("по настроению", "mood"),
    ("по языку", "language"),
    ("по артисту", "artist"),
    ("треки исполнителя", "artist"),
)
_VERBS = ("включ", "запуст", "играй", "поставь")
_WAVE_WORDS = frozenset({"волна", "волну", "волны"})
_MY = frozenset({"моя", "мою", "моей", "мое"})
_FILLERS = frozenset({"пятница", "пожалуйста", "давай", "ну"})
# Before the wave word these mean a song, band or album, not a wave card.
_MUSIC_MARKERS = (
    "песн",
    "трек",
    "композици",
    "исполнител",
    "артист",
    "певц",
    "певиц",
    "групп",
    "альбом",
)
_STOP = frozenset(
    {
        "по",
        "под",
        "про",
        "для",
        "жанру",
        "жанр",
        "артисту",
        "артиста",
        "исполнителя",
        "занятие",
        "характеру",
        "характер",
        "настроению",
        "настроение",
        "языку",
        "язык",
    }
)


@dataclass(frozen=True)
class WaveCard:
    name: str  # full UI name, spaces normalized
    kind: str  # genre / activity / character / mood / artist / other
    title: str  # the short title a person says


def _fold(text: str) -> str:
    return text.lower().replace("ё", "е")


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", _fold(text.replace("\xa0", " ")))


def parse_card(name: str) -> WaveCard | None:
    """A WaveCard for a wave card name, None for anything that is not a wave."""
    text = " ".join((name or "").replace("\xa0", " ").split())
    if not _fold(text).startswith(WAVE_PREFIX):
        return None
    rest = text[len(WAVE_PREFIX) :]
    if rest and not rest[0].isspace():
        return None
    rest = rest.lstrip(" \u2014\u2013-:")
    kind, title = "other", rest
    folded = _fold(rest)
    for marker, marker_kind in _KINDS:
        if folded.startswith(marker + " "):
            kind, title = marker_kind, rest[len(marker) :]
            break
    title = title.strip()
    if not title:
        return None
    return WaveCard(name=text, kind=kind, title=title)


def cards_from_names(names: Iterable[str]) -> list[WaveCard]:
    """Wave cards from UI names: non-waves dropped, copies of one card merged."""
    cards: list[WaveCard] = []
    seen: set[str] = set()
    for name in names:
        card = parse_card(name)
        if card is None or card.name in seen:
            continue
        seen.add(card.name)
        cards.append(card)
    return cards


def parse_wave_card_request(text: str) -> str | None:
    """The spoken title from "включи волну <title>", None if it is not such a request.

    None for the plain "включи мою волну" (no title) and for phrases without a
    play verb or without exactly one wave word.
    """
    words = _tokens(text)
    if len(words) > MAX_REQUEST_WORDS:
        return None
    if not any(word.startswith(_VERBS) for word in words):
        return None
    if sum(1 for word in words if word in _WAVE_WORDS) != 1:
        return None
    wave_at = next(i for i, word in enumerate(words) if word in _WAVE_WORDS)
    if any(word.startswith(_MUSIC_MARKERS) for word in words[:wave_at]):
        return None
    query = [
        word
        for word in words
        if not word.startswith(_VERBS)
        and word not in _WAVE_WORDS
        and word not in _MY
        and word not in _FILLERS
        and word not in _STOP
    ]
    if not query:
        return None
    result = " ".join(query)
    log.info("wave card request from %r", text)
    return result


def _word_score(spoken: str, title_word: str) -> int:
    if spoken == title_word:
        return 3
    common = 0
    for first, second in zip(spoken, title_word):
        if first != second:
            break
        common += 1
    if common >= 3 and common >= min(len(spoken), len(title_word)) - 2:
        return 1
    return 0


def _score(query: list[str], title: list[str]) -> int | None:
    """Total score, None if some spoken word matches no word of the title."""
    total = 0
    for spoken in query:
        best = max((_word_score(spoken, word) for word in title), default=0)
        if best == 0:
            return None
        total += best
    if query == title:
        total += EXACT_TITLE_BONUS
    return total


def pick_card(query: str, cards: list[WaveCard]) -> WaveCard | None:
    """The best card for a spoken title, None if no card has all the words."""
    spoken = [word for word in _tokens(query) if word not in _STOP]
    if not spoken:
        return None
    best: WaveCard | None = None
    best_key: tuple[int, int, int] | None = None
    for index, card in enumerate(cards):
        title = _tokens(card.title)
        score = _score(spoken, title)
        if score is None:
            continue
        key = (score, -len(title), -index)
        if best_key is None or key > best_key:
            best, best_key = card, key
    return best
