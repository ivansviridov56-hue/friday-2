"""Glue: "what is on the screen" phrase -> screenshot -> vision model -> spoken answer.

Never returns None for a recognized request, even when something breaks:
otherwise the phrase would fall through to the LLM, which cannot see the screen
and would invent an answer. The screenshot is taken first, then a short
"looking" phrase is spoken in the background while the vision model works.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from friday.assistant import CommandReply
from friday.llm import AllProvidersFailed, Reply
from friday.screen_capture import ScreenCaptureError, Screenshot
from friday.screen_request import is_screen_request

log = logging.getLogger(__name__)

Handler = Callable[[str], CommandReply | None]

ANNOUNCE_PHRASE = "Смотрю экран."
_NO_CAPTURE = "Не получилось снять экран."
_NO_BRAIN = "Не получилось рассмотреть экран: нейросеть недоступна."
_FALLBACK = "Не получилось посмотреть на экран."
_ANNOUNCE_JOIN_S = 10.0


def _announce_in_background(
    announce: Callable[[str], object] | None,
) -> threading.Thread | None:
    if announce is None:
        return None

    def run() -> None:
        try:
            announce(ANNOUNCE_PHRASE)
        except Exception:  # a broken speaker must not break the answer
            log.exception("announce failed")

    thread = threading.Thread(target=run, name="screen-announce", daemon=True)
    thread.start()
    return thread


def make_screen_handler(
    capture: Callable[[], Screenshot],
    describe: Callable[[Screenshot, str], Reply],
    announce: Callable[[str], object] | None = None,
) -> Handler:
    def handle(text: str) -> CommandReply | None:
        if not is_screen_request(text):
            return None
        thread = None
        try:
            shot = capture()
            thread = _announce_in_background(announce)
            answer = describe(shot, text).text.strip() or _FALLBACK
        except ScreenCaptureError as exc:
            log.warning("screen capture failed: %s", exc)
            answer = _NO_CAPTURE
        except AllProvidersFailed as exc:
            log.warning("vision failed: %s", exc)
            answer = _NO_BRAIN
        except Exception:
            log.exception("screen request failed")
            answer = _FALLBACK
        if thread is not None:
            thread.join(timeout=_ANNOUNCE_JOIN_S)  # do not talk over "Смотрю экран"
        return CommandReply(answer, spoken=True)

    return handle
