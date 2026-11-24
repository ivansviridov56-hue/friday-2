from types import SimpleNamespace
from typing import Any, cast

from friday.assistant import Assistant, CommandReply
from friday.ui_events import MessageAdded, UiEventBus


class FakeBrain:
    def ask(self, messages):
        return SimpleNamespace(text="ok")


def build(commands=None):
    bus = UiEventBus()
    seen = []
    bus.subscribe(seen.append)
    assistant = Assistant(
        stt=cast(Any, None),
        llm=cast(Any, FakeBrain()),
        speak=lambda text: None,
        system_prompt="x",
        events=bus,
        commands=commands,
    )
    return assistant, seen


def assistant_messages(seen):
    return [e for e in seen if isinstance(e, MessageAdded) and e.role == "assistant"]


def test_command_reply_that_is_not_spoken_is_marked():
    assistant, seen = build(lambda heard: CommandReply("Включаю.", spoken=False))
    assistant.handle_text("дальше")
    assert [m.spoken for m in assistant_messages(seen)] == [False]


def test_command_reply_that_is_spoken_is_marked():
    assistant, seen = build(lambda heard: CommandReply("Играет такая-то.", spoken=True))
    assistant.handle_text("что играет")
    assert [m.spoken for m in assistant_messages(seen)] == [True]


def test_llm_reply_is_spoken():
    assistant, seen = build()
    assistant.handle_text("привет")
    assert [m.spoken for m in assistant_messages(seen)] == [True]
