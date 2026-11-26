"""Glue: "play My Wave with a mood" phrase -> start it -> spoken answer.

Like the other handlers, it never returns None for a recognized request, even
when something breaks: otherwise the phrase would fall through to the LLM.
A phrase without a mood returns None and goes on to the plain My Wave handler.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.assistant import CommandReply
from friday.wave_mood import MOOD_NAMES, MoodStatus
from friday.wave_request import parse_wave_mood

logger = logging.getLogger(__name__)

Handler = Callable[[str], CommandReply | None]

_ANSWERS = {
    MoodStatus.ALREADY_SET: "Эта волна уже играет.",
    MoodStatus.NO_WINDOW: "Не вижу окно Яндекс Музыки.",
    MoodStatus.NO_PANEL: (
        "Не нашла настройки Моей волны. Открой Мою волну в приложении."
    ),
    MoodStatus.NOT_CONFIRMED: "Нажала, но волна не заиграла.",
}
_FALLBACK = "Не получилось включить Мою волну с настроением."


class MoodStarter(Protocol):
    def launch(self, mood: str) -> MoodStatus: ...


def _answer(status: MoodStatus, mood: str) -> str:
    if status is MoodStatus.STARTED:
        return f"Включаю Мою волну, настроение: {MOOD_NAMES[mood].lower()}."
    return _ANSWERS.get(status, _FALLBACK)


def make_wave_mood_handler(launcher: MoodStarter) -> Handler:
    def handle(text: str) -> CommandReply | None:
        mood = parse_wave_mood(text)
        if mood is None:
            return None
        try:
            status = launcher.launch(mood)
        except Exception:
            logger.exception("wave mood request failed")
            return CommandReply(_FALLBACK, spoken=True)
        return CommandReply(_answer(status, mood), spoken=True)

    return handle
