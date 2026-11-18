"""Tests for the memory phrase parser (stage 8b)."""

import pytest

from friday.memory_request import MemoryAction, MemoryRequest, parse_memory_request


def remember(text: str) -> MemoryRequest:
    return MemoryRequest(MemoryAction.REMEMBER, text)


def forget(text: str) -> MemoryRequest:
    return MemoryRequest(MemoryAction.FORGET, text)


RECALL = MemoryRequest(MemoryAction.RECALL, "")


@pytest.mark.parametrize(
    ("phrase", "fact"),
    [
        ("Запомни, что меня зовут Иван.", "меня зовут Иван"),
        ("запомни: я люблю кофе", "я люблю кофе"),
        ("Запомни пожалуйста, что у меня есть кошка Муся!", "у меня есть кошка Муся"),
        ("запомни мой день рождения 5 мая", "мой день рождения 5 мая"),
        ("Запомните, что я живу в Минске", "я живу в Минске"),
        ("Запомни что кошку зовут Муся", "кошку зовут Муся"),
        ("запомни, чтобы я не забыл", "чтобы я не забыл"),
        ("  Запомни,   что я   люблю чай.  ", "я люблю чай"),
    ],
)
def test_remember_phrases(phrase: str, fact: str) -> None:
    assert parse_memory_request(phrase) == remember(fact)


@pytest.mark.parametrize(
    "phrase", ["Запомни.", "запомни", "Запомни, что", "запомни пожалуйста"]
)
def test_remember_without_a_fact_is_still_a_request_with_empty_text(
    phrase: str,
) -> None:
    assert parse_memory_request(phrase) == remember("")


@pytest.mark.parametrize(
    ("phrase", "query"),
    [
        ("Забудь, что я люблю кофе", "я люблю кофе"),
        ("Забудь про кошку", "кошку"),
        ("забудь мой день рождения", "мой день рождения"),
        ("Забудьте про кофе.", "кофе"),
        ("Забудь о том, что я люблю кофе", "я люблю кофе"),
        ("забудь об имени Муся", "имени Муся"),
    ],
)
def test_forget_phrases(phrase: str, query: str) -> None:
    assert parse_memory_request(phrase) == forget(query)


@pytest.mark.parametrize(
    "phrase",
    [
        "Забудь.",
        "забудь",
        "Забудь всё",
        "забудь все",
        "Забудь об этом",
        "забудь про это",
        "Забудь я",
    ],
)
def test_forget_with_generic_or_tiny_query_asks_what_to_forget(phrase: str) -> None:
    # A generic word such as "всё" must never become a substring search.
    assert parse_memory_request(phrase) == forget("")


@pytest.mark.parametrize(
    "phrase",
    [
        "Что ты обо мне помнишь?",
        "Что ты помнишь обо мне",
        "что ты знаешь обо мне",
        "Расскажи, что ты помнишь про меня",
        "Что ты про меня знаешь?",
        "Что ты обо мне знаешь.",
    ],
)
def test_recall_phrases(phrase: str) -> None:
    assert parse_memory_request(phrase) == RECALL


@pytest.mark.parametrize(
    "phrase",
    [
        "",
        "   ",
        "Привет, как дела?",
        "Что ты помнишь?",
        "Что ты знаешь о Пушкине?",
        "Расскажи обо мне анекдот",
        "Что ты обо мне помнишь из того, что я рассказывал тебе вчера вечером",
        "Я не запомнил дорогу",
        "Запомнить это сложно",
        "Скажи, запомни что-нибудь",
        "Помнишь, как мы гуляли?",
        "Я забыл ключи",
        "Давай забудь про это",
        "Забывчивость - это плохо",
        "Включи песню Полетели",
    ],
)
def test_other_speech_is_not_a_memory_request(phrase: str) -> None:
    assert parse_memory_request(phrase) is None
