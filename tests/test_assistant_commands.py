from types import SimpleNamespace

import numpy as np

from friday.assistant import Assistant, CommandReply
from friday.ui_events import MessageAdded, State, StateChanged, UiEventBus

AUDIO = np.zeros(10, dtype=np.float32)


class FakeStt:
    def __init__(self, text):
        self._text = text

    def transcribe(self, audio):
        return self._text


class FakeLlm:
    def __init__(self):
        self.calls = 0

    def ask(self, messages):
        self.calls += 1
        return SimpleNamespace(text="ответ", provider="fake", latency_ms=1)


class SpyHistory:
    def __init__(self):
        self.added = []

    def messages_with(self, text):
        return [{"role": "user", "content": text}]

    def add_exchange(self, heard, reply):
        self.added.append((heard, reply))


def make(stt_text, commands):
    bus = UiEventBus()
    events = []
    bus.subscribe(events.append)
    llm = FakeLlm()
    history = SpyHistory()
    spoken = []
    assistant = Assistant(
        FakeStt(stt_text),
        llm,  # pyright: ignore[reportArgumentType]
        spoken.append,
        system_prompt="sys",
        history=history,  # pyright: ignore[reportArgumentType]
        events=bus,
        commands=commands,
    )
    return assistant, llm, history, spoken, events


def test_command_is_answered_locally_without_the_llm():
    assistant, llm, _history, spoken, events = make(
        "пауза", lambda text: CommandReply("Не вижу Яндекс Музыку.")
    )
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert turn.local_reply == "Не вижу Яндекс Музыку."
    assert turn.reply is None
    assert llm.calls == 0
    assert spoken == ["Не вижу Яндекс Музыку."]
    assert events == [
        StateChanged(State.THINKING),
        MessageAdded("user", "пауза"),
        MessageAdded("assistant", "Не вижу Яндекс Музыку."),
        StateChanged(State.SPEAKING),
        StateChanged(State.IDLE),
    ]


def test_silent_command_is_shown_but_not_spoken():
    assistant, llm, _history, spoken, events = make(
        "пауза", lambda text: CommandReply("Поставила на паузу.", spoken=False)
    )
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert turn.local_reply == "Поставила на паузу."
    assert llm.calls == 0
    assert spoken == []
    assert events == [
        StateChanged(State.THINKING),
        MessageAdded("user", "пауза"),
        MessageAdded("assistant", "Поставила на паузу.", spoken=False),
        StateChanged(State.IDLE),
    ]


def test_command_exchange_is_not_stored_in_history():
    assistant, _llm, history, _spoken, _events = make(
        "пауза", lambda text: CommandReply("ок")
    )
    assistant.handle_audio(AUDIO)
    assert history.added == []


def test_ordinary_speech_goes_to_the_llm_and_is_stored():
    assistant, llm, history, spoken, _events = make("привет", lambda text: None)
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert llm.calls == 1
    assert turn.local_reply is None
    assert history.added == [("привет", "ответ")]
    assert spoken == ["ответ"]


def test_broken_command_handler_falls_back_to_the_llm():
    def broken(_text):
        raise RuntimeError("boom")

    assistant, llm, _history, spoken, _events = make("привет", broken)
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert llm.calls == 1
    assert turn.reply is not None
    assert spoken == ["ответ"]
