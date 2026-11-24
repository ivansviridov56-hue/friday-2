"""One voice turn: audio -> text -> LLM -> spoken reply."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Protocol

import numpy as np

from friday.history import ConversationHistory
from friday.llm import AllProvidersFailed, Reply
from friday.ui_events import MessageAdded, State, StateChanged, UiEventBus

log = logging.getLogger(__name__)

FAILURE_PHRASE = "Не получилось достучаться до нейросети. Попробуй ещё раз."


class Transcriber(Protocol):
    def transcribe(self, audio: np.ndarray) -> str: ...


class Brain(Protocol):
    def ask(self, messages: list[dict]) -> Reply: ...


@dataclass(frozen=True)
class CommandReply:
    """Answer of a local command. `spoken=False`: show it in the window only."""

    text: str
    spoken: bool = True


@dataclass(frozen=True)
class Turn:
    heard: str
    reply: Reply | None  # None when every LLM provider failed or a command answered
    local_reply: str | None = None  # answer of a local command (no LLM involved)


class Assistant:
    def __init__(
        self,
        stt: Transcriber,
        llm: Brain,
        speak: Callable[[str], object],
        system_prompt: str | Callable[[], str],
        history: ConversationHistory | None = None,
        failure_phrase: str = FAILURE_PHRASE,
        events: UiEventBus | None = None,
        commands: Callable[[str], CommandReply | None] | None = None,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._speak = speak
        self._system_prompt = system_prompt
        self._history = history if history is not None else ConversationHistory()
        self._failure_phrase = failure_phrase
        self._events = events or UiEventBus()
        self._commands = commands

    def handle_audio(self, audio: np.ndarray) -> Turn | None:
        """Run one turn. Returns None if nothing was heard."""
        self._set_state(State.THINKING)
        try:
            return self._run_turn(audio)
        finally:
            self._set_state(State.IDLE)

    def handle_text(self, text: str) -> Turn | None:
        """Run one turn from an already recognized phrase (the wake word path)."""
        self._set_state(State.THINKING)
        try:
            return self._run_text(text.strip())
        finally:
            self._set_state(State.IDLE)

    def _run_turn(self, audio: np.ndarray) -> Turn | None:
        return self._run_text(self._stt.transcribe(audio).strip())

    def _run_text(self, heard: str) -> Turn | None:
        if not heard:
            log.info("nothing heard")
            return None
        self._events.publish(MessageAdded("user", heard))
        local = self._try_command(heard)
        if local is not None:
            self._events.publish(
                MessageAdded("assistant", local.text, spoken=local.spoken)
            )
            if local.spoken:
                self._say(local.text)
            return Turn(heard, None, local_reply=local.text)

        messages = [{"role": "system", "content": self._current_system_prompt()}]
        messages += self._history.messages_with(heard)
        try:
            reply = self._llm.ask(messages)
        except AllProvidersFailed as exc:
            log.warning("all providers failed: %s", exc)
            self._events.publish(MessageAdded("assistant", self._failure_phrase))
            self._say(self._failure_phrase)
            return Turn(heard, None)

        # before speaking: keep it even if TTS fails
        self._history.add_exchange(heard, reply.text)
        self._events.publish(MessageAdded("assistant", reply.text))
        self._say(reply.text)
        return Turn(heard, reply)

    def _current_system_prompt(self) -> str:
        """The prompt may be a function, so it can reflect what changed since the last turn."""
        source = self._system_prompt
        return source() if callable(source) else source

    def _try_command(self, heard: str) -> CommandReply | None:
        if self._commands is None:
            return None
        try:
            return self._commands(heard)
        except Exception:  # a broken command must not kill the turn
            log.exception("command handler failed")
            return None

    def _say(self, text: str) -> None:
        self._set_state(State.SPEAKING)
        try:
            self._speak(text)
        except Exception:  # a broken speaker must not kill the loop
            log.exception("speech failed")

    def _set_state(self, state: State) -> None:
        self._events.publish(StateChanged(state))
