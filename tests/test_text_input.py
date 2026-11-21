import logging

import pytest

from friday.text_input import TextInput, WindowApi


def make_input(result: bool = True, max_length: int = 500):
    received: list[str] = []

    def handler(text: str) -> bool:
        received.append(text)
        return result

    text_input = TextInput(max_length=max_length)
    text_input.set_handler(handler)
    return text_input, received


def test_text_is_stripped_and_passed_on():
    text_input, received = make_input()
    assert text_input.submit("  привет  ") is True
    assert received == ["привет"]


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_text_is_rejected(text):
    text_input, received = make_input()
    assert text_input.submit(text) is False
    assert received == []


def test_without_handler_text_is_rejected():
    assert TextInput().submit("привет") is False


def test_handler_refusal_is_returned():
    text_input, received = make_input(result=False)
    assert text_input.submit("привет") is False
    assert received == ["привет"]


def test_too_long_text_is_rejected():
    text_input, received = make_input(max_length=5)
    assert text_input.submit("123456") is False
    assert received == []


def test_text_of_max_length_is_accepted():
    text_input, received = make_input(max_length=5)
    assert text_input.submit("12345") is True
    assert received == ["12345"]


def test_broken_handler_does_not_raise():
    text_input = TextInput()

    def broken(text: str) -> bool:
        raise RuntimeError("boom")

    text_input.set_handler(broken)
    assert text_input.submit("привет") is False


def test_handler_can_be_cleared():
    text_input, received = make_input()
    text_input.set_handler(None)
    assert text_input.submit("привет") is False
    assert received == []


def test_zero_max_length_is_a_mistake():
    with pytest.raises(ValueError):
        TextInput(max_length=0)


def test_text_is_never_logged(caplog):
    caplog.set_level(logging.DEBUG)
    TextInput(max_length=3).submit("секретный")
    TextInput().submit("секретный")
    assert "секретный" not in caplog.text


def test_window_api_forwards_text():
    text_input, received = make_input()
    assert WindowApi(text_input).submit_text("привет") is True
    assert received == ["привет"]


@pytest.mark.parametrize("value", [None, 5, ["a"]])
def test_window_api_rejects_non_text(value):
    text_input, received = make_input()
    assert WindowApi(text_input).submit_text(value) is False
    assert received == []
