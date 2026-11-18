from friday.llm import AllProvidersFailed, Reply
from friday.screen_capture import ScreenCaptureError, Screenshot
from friday.screen_handler import ANNOUNCE_PHRASE, make_screen_handler

SHOT = Screenshot(
    data=b"\xff\xd8jpeg",
    mime="image/jpeg",
    width=1536,
    height=960,
    source_width=1920,
    source_height=1200,
)
ANSWER = Reply("На экране редактор.", "fake", 5)


class Spy:
    """Records capture / describe / announce calls."""

    def __init__(
        self,
        capture: Screenshot | Exception = SHOT,
        describe: Reply | Exception = ANSWER,
        announce_error: Exception | None = None,
    ) -> None:
        self.events: list[str] = []
        self.questions: list[str] = []
        self._capture = capture
        self._describe = describe
        self._announce_error = announce_error

    def capture(self) -> Screenshot:
        self.events.append("capture")
        if isinstance(self._capture, Exception):
            raise self._capture
        return self._capture

    def describe(self, shot: Screenshot, question: str) -> Reply:
        self.events.append("describe")
        self.questions.append(question)
        if isinstance(self._describe, Exception):
            raise self._describe
        return self._describe

    def announce(self, text: str) -> None:
        self.events.append(f"announce:{text}")
        if self._announce_error is not None:
            raise self._announce_error


def test_answer_is_spoken_and_announced_before_returning() -> None:
    spy = Spy()
    handler = make_screen_handler(spy.capture, spy.describe, spy.announce)
    reply = handler("Что на экране?")
    assert reply is not None
    assert reply.text == "На экране редактор."
    assert reply.spoken is True
    assert spy.events[0] == "capture"
    assert len(spy.events) == 3
    assert set(spy.events) == {"capture", "describe", f"announce:{ANNOUNCE_PHRASE}"}


def test_question_is_the_heard_phrase() -> None:
    spy = Spy()
    make_screen_handler(spy.capture, spy.describe, spy.announce)(
        "Что у меня на экране?"
    )
    assert spy.questions == ["Что у меня на экране?"]


def test_capture_error_is_spoken_and_nothing_is_announced() -> None:
    spy = Spy(capture=ScreenCaptureError("boom"))
    handler = make_screen_handler(spy.capture, spy.describe, spy.announce)
    reply = handler("Что на экране?")
    assert reply is not None
    assert reply.spoken is True
    assert "снять" in reply.text
    assert spy.events == ["capture"]


def test_all_providers_failed_is_spoken() -> None:
    error = AllProvidersFailed({"cf-mistral": "HTTP 500"})
    spy = Spy(describe=error)
    reply = make_screen_handler(spy.capture, spy.describe, spy.announce)("Опиши экран")
    assert reply is not None
    assert reply.spoken is True
    assert "нейросеть" in reply.text


def test_unexpected_error_is_spoken_not_raised() -> None:
    spy = Spy(describe=RuntimeError("boom"))
    reply = make_screen_handler(spy.capture, spy.describe, spy.announce)("Опиши экран")
    assert reply is not None
    assert reply.spoken is True
    assert reply.text


def test_broken_announce_does_not_break_the_answer() -> None:
    spy = Spy(announce_error=RuntimeError("speaker broke"))
    reply = make_screen_handler(spy.capture, spy.describe, spy.announce)(
        "Что на экране?"
    )
    assert reply is not None
    assert reply.text == "На экране редактор."


def test_works_without_announce() -> None:
    spy = Spy()
    reply = make_screen_handler(spy.capture, spy.describe)("Что на экране?")
    assert reply is not None
    assert reply.text == "На экране редактор."
    assert spy.events == ["capture", "describe"]


def test_other_phrases_return_none_and_do_not_capture() -> None:
    spy = Spy()
    handler = make_screen_handler(spy.capture, spy.describe, spy.announce)
    assert handler("Включи свет") is None
    assert handler("Что такое экран") is None
    assert spy.events == []
