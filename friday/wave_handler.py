"""Glue: "play My Wave" phrase -> start the wave -> spoken answer.

Like the play handler, it never returns None for a recognized request, even
when something breaks: otherwise the phrase would fall through to the LLM and
Friday would chat about the wave instead of saying why it did not start.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from friday.assistant import CommandReply
from friday.wave_launcher import WaveStatus
from friday.wave_request import is_wave_request

logger = logging.getLogger(__name__)

Handler = Callable[[str], CommandReply | None]

_ANSWERS = {
    WaveStatus.STARTED: "Включаю Мою волну",
    WaveStatus.ALREADY_PLAYING: "Музыка уже играет.",
    WaveStatus.NO_PLAYER: "Не вижу плеер Моей волны. Открой Мою волну в приложении.",
    WaveStatus.NOT_CONFIRMED: "Нажала, но Моя волна не заиграла.",
}
_FALLBACK = "Не получилось включить Мою волну."


class WaveStarter(Protocol):
    def launch(self) -> WaveStatus: ...


def make_wave_handler(launcher: WaveStarter) -> Handler:
    def handle(text: str) -> CommandReply | None:
        if not is_wave_request(text):
            return None
        try:
            status = launcher.launch()
        except Exception:
            logger.exception("wave request failed")
            return CommandReply(_FALLBACK, spoken=True)
        return CommandReply(_ANSWERS.get(status, _FALLBACK), spoken=True)

    return handle
