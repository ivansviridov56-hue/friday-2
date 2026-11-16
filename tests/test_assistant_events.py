from types import SimpleNamespace

import numpy as np

from friday.assistant import FAILURE_PHRASE, Assistant
from friday.llm import AllProvidersFailed
from friday.ui_events import MessageAdded, State, StateChanged, UiEventBus

AUDIO = np.zeros(10, dtype=np.float32)


class FakeStt:
    def __init__(self, text):
        self._text = text

    def transcribe(self, audio):
        return self._text


class FakeLlm:
    def __init__(self, text=None, error=None):
        self._text = text
        self._error = error

    def ask(self, messages):
        if self._error:
            raise self._error
        return SimpleNamespace(text=self._text, provider="fake", latency_ms=1)


def make(stt_text, llm, speak=lambda text: None):
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    assistant = Assistant(
        FakeStt(stt_text), llm, speak, system_prompt="sys", events=bus
    )
    return assistant, got


def test_successful_turn_events():
    assistant, got = make("привет", FakeLlm("здравствуй"))
    assistant.handle_audio(AUDIO)
    assert got == [
        StateChanged(State.THINKING),
        MessageAdded("user", "привет"),
        MessageAdded("assistant", "здравствуй"),
        StateChanged(State.SPEAKING),
        StateChanged(State.IDLE),
    ]


def test_nothing_heard_returns_to_idle_without_messages():
    spoken = []
    assistant, got = make("   ", FakeLlm("x"), speak=spoken.append)
    assert assistant.handle_audio(AUDIO) is None
    assert got == [StateChanged(State.THINKING), StateChanged(State.IDLE)]
    assert spoken == []


def test_failed_llm_shows_failure_phrase():
    assistant, got = make("привет", FakeLlm(error=AllProvidersFailed({"fake": "down"})))
    assistant.handle_audio(AUDIO)
    assert got == [
        StateChanged(State.THINKING),
        MessageAdded("user", "привет"),
        MessageAdded("assistant", FAILURE_PHRASE),
        StateChanged(State.SPEAKING),
        StateChanged(State.IDLE),
    ]


def test_broken_speaker_still_ends_idle():
    def broken(_text):
        raise RuntimeError("no sound")

    assistant, got = make("привет", FakeLlm("ответ"), speak=broken)
    assistant.handle_audio(AUDIO)
    assert got[-1] == StateChanged(State.IDLE)
