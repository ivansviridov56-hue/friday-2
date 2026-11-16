"""One voice turn: audio -> text -> LLM -> spoken reply."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Protocol

import numpy as np

from friday.history import ConversationHistory
from friday.llm import AllProvidersFailed, Reply

log = logging.getLogger(__name__)

FAILURE_PHRASE = "Не получилось достучаться до нейросети. Попробуй ещё раз."


class Transcriber(Protocol):
    def transcribe(self, audio: np.ndarray) -> str: ...


class Brain(Protocol):
    def ask(self, messages: list[dict]) -> Reply: ...


@dataclass(frozen=True)
class Turn:
    heard: str
    reply: Reply | None  # None when every LLM provider failed


class Assistant:
    def __init__(
        self,
        stt: Transcriber,
        llm: Brain,
        speak: Callable[[str], object],
        system_prompt: str,
        history: ConversationHistory | None = None,
        failure_phrase: str = FAILURE_PHRASE,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._speak = speak
        self._system_prompt = system_prompt
        self._history = history or ConversationHistory()
        self._failure_phrase = failure_phrase

    def handle_audio(self, audio: np.ndarray) -> Turn | None:
        """Run one turn. Returns None if nothing was heard."""
        heard = self._stt.transcribe(audio).strip()
        if not heard:
            log.info("nothing heard")
            return None

        messages = [{"role": "system", "content": self._system_prompt}]
        messages += self._history.messages_with(heard)
        try:
            reply = self._llm.ask(messages)
        except AllProvidersFailed as exc:
            log.warning("all providers failed: %s", exc)
            self._say(self._failure_phrase)
            return Turn(heard, None)

        self._history.add_exchange(
            heard, reply.text
        )  # before speaking: keep it even if TTS fails
        self._say(reply.text)
        return Turn(heard, reply)

    def _say(self, text: str) -> None:
        try:
            self._speak(text)
        except Exception:  # a broken speaker must not kill the loop
            log.exception("speech failed")
