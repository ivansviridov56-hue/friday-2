import numpy as np

from friday.history import ConversationHistory
from friday.assistant import FAILURE_PHRASE, Assistant, CommandReply
from friday.llm import AllProvidersFailed, Reply

AUDIO = np.ones(16000, dtype=np.float32)


class FakeStt:
    def __init__(self, *texts: str) -> None:
        self.texts = list(texts)

    def transcribe(self, audio) -> str:
        return self.texts.pop(0)


class FakeLlm:
    def __init__(self, *outcomes) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[list[dict]] = []

    def ask(self, messages):
        self.calls.append([dict(m) for m in messages])
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return Reply(outcome, "fake", 10)


def make(stt, llm, speak=None):
    spoken: list[str] = []
    assistant = Assistant(stt, llm, speak or spoken.append, system_prompt="SYS")
    return assistant, spoken


def contents(messages: list[dict]) -> list[str]:
    return [m["content"] for m in messages]


def test_silence_does_nothing() -> None:
    llm = FakeLlm()
    assistant, spoken = make(FakeStt("", "   "), llm)
    assert assistant.handle_audio(AUDIO) is None
    assert assistant.handle_audio(AUDIO) is None
    assert llm.calls == [] and spoken == []


def test_happy_path_sends_system_and_user_then_speaks() -> None:
    llm = FakeLlm("Привет!")
    assistant, spoken = make(FakeStt(" Привет, Пятница "), llm)
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert turn.reply is not None
    assert llm.calls == [
        [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "Привет, Пятница"},
        ]
    ]
    assert spoken == ["Привет!"]
    assert turn.heard == "Привет, Пятница" and turn.reply.text == "Привет!"


def test_second_turn_includes_first_exchange() -> None:
    llm = FakeLlm("a1", "a2")
    assistant, _ = make(FakeStt("q1", "q2"), llm)
    assistant.handle_audio(AUDIO)
    assistant.handle_audio(AUDIO)
    assert contents(llm.calls[1]) == ["SYS", "q1", "a1", "q2"]


def test_failure_speaks_phrase_and_keeps_history_clean() -> None:
    llm = FakeLlm(AllProvidersFailed({"cf": "HTTP 500"}), "a2")
    assistant, spoken = make(FakeStt("q1", "q2"), llm)
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert turn.heard == "q1" and turn.reply is None
    assert spoken == [FAILURE_PHRASE]
    assistant.handle_audio(AUDIO)
    assert contents(llm.calls[1]) == ["SYS", "q2"]


def test_speech_failure_does_not_lose_the_exchange() -> None:
    def broken(text: str) -> None:
        raise RuntimeError("no audio device")

    llm = FakeLlm("a1", "a2")
    assistant, _ = make(FakeStt("q1", "q2"), llm, speak=broken)
    turn = assistant.handle_audio(AUDIO)
    assert turn is not None
    assert turn.reply is not None
    assert turn.reply.text == "a1"
    assistant.handle_audio(AUDIO)
    assert contents(llm.calls[1]) == ["SYS", "q1", "a1", "q2"]


def test_system_prompt_can_be_a_function_called_every_turn() -> None:
    llm = FakeLlm("a1", "a2")
    prompts = iter(["SYS1", "SYS2"])
    assistant = Assistant(
        FakeStt("q1", "q2"),
        llm,
        lambda text: None,
        system_prompt=lambda: next(prompts),
    )
    assistant.handle_audio(AUDIO)
    assistant.handle_audio(AUDIO)
    assert llm.calls[0][0] == {"role": "system", "content": "SYS1"}
    assert llm.calls[1][0] == {"role": "system", "content": "SYS2"}


def test_prompt_function_is_not_called_for_local_commands() -> None:
    built: list[int] = []

    def build() -> str:
        built.append(1)
        return "SYS"

    assistant = Assistant(
        FakeStt("q"),
        FakeLlm(),
        lambda text: None,
        system_prompt=build,
        commands=lambda text: CommandReply("ok", spoken=False),
    )
    assistant.handle_audio(AUDIO)
    assert built == []


def test_assistant_uses_the_given_empty_history() -> None:
    history = ConversationHistory()
    assistant = Assistant(
        FakeStt("q1"),
        FakeLlm("a1"),
        lambda text: None,
        system_prompt="SYS",
        history=history,
    )
    assistant.handle_audio(AUDIO)
    assert len(history) == 1


def test_clearing_the_given_history_removes_it_from_the_next_request() -> None:
    history = ConversationHistory()
    llm = FakeLlm("a1", "a2")
    assistant = Assistant(
        FakeStt("q1", "q2"),
        llm,
        lambda text: None,
        system_prompt="SYS",
        history=history,
    )
    assistant.handle_audio(AUDIO)
    history.clear()
    assistant.handle_audio(AUDIO)
    assert len(llm.calls[1]) == 2
