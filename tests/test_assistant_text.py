import numpy as np

from friday.assistant import Assistant, CommandReply
from friday.llm import Reply


class FakeStt:
    def __init__(self, text: str = "что слышно") -> None:
        self.text = text
        self.calls = 0

    def transcribe(self, audio: np.ndarray) -> str:
        self.calls += 1
        return self.text


class FakeLlm:
    def __init__(self) -> None:
        self.asked: list[list[dict]] = []

    def ask(self, messages: list[dict]) -> Reply:
        self.asked.append(messages)
        return Reply("Ответ", "fake", 5)


def make(stt: FakeStt | None = None, commands=None):
    spoken: list[str] = []
    llm = FakeLlm()
    stt = stt or FakeStt()
    assistant = Assistant(stt, llm, spoken.append, "system", commands=commands)
    return assistant, stt, llm, spoken


def test_handle_text_answers_without_recognition() -> None:
    assistant, stt, llm, spoken = make()
    turn = assistant.handle_text("  Расскажи анекдот ")
    assert turn is not None and turn.heard == "Расскажи анекдот"
    assert stt.calls == 0
    assert llm.asked[0][-1] == {"role": "user", "content": "Расскажи анекдот"}
    assert spoken == ["Ответ"]


def test_handle_text_with_nothing_returns_none() -> None:
    assistant, _, llm, spoken = make()
    assert assistant.handle_text("   ") is None
    assert llm.asked == [] and spoken == []


def test_handle_text_tries_local_commands_first() -> None:
    assistant, _, llm, spoken = make(
        commands=lambda text: CommandReply("Пауза") if text == "пауза" else None
    )
    turn = assistant.handle_text("пауза")
    assert turn is not None and turn.local_reply == "Пауза"
    assert llm.asked == [] and spoken == ["Пауза"]


def test_handle_text_is_remembered_in_the_dialogue() -> None:
    assistant, _, llm, _ = make()
    assistant.handle_text("первый вопрос")
    assistant.handle_text("второй вопрос")
    contents = [m["content"] for m in llm.asked[1]]
    assert "первый вопрос" in contents and "Ответ" in contents


def test_handle_audio_still_recognizes_the_phrase() -> None:
    assistant, stt, llm, _ = make(FakeStt("Привет"))
    turn = assistant.handle_audio(np.zeros(10, dtype=np.float32))
    assert turn is not None and turn.heard == "Привет"
    assert stt.calls == 1
    assert llm.asked[0][-1]["content"] == "Привет"
