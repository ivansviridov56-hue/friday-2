from __future__ import annotations

import pytest

from friday.assistant import CommandReply
from friday.memory_handler import Handler, make_memory_handler
from friday.memory_store import AddStatus, MemoryStore


def _reply(handle: Handler, phrase: str) -> CommandReply:
    """Run a phrase that must be recognized as a memory command."""
    reply = handle(phrase)
    assert reply is not None
    return reply


@pytest.fixture
def store(tmp_path) -> MemoryStore:
    return MemoryStore(tmp_path / "facts.json")


def test_ordinary_speech_is_not_hijacked(store):
    handle = make_memory_handler(store)
    for phrase in (
        "Привет, как дела?",
        "Что ты знаешь о Пушкине?",
        "Я не запомнил дорогу",
        "Включи свет",
    ):
        assert handle(phrase) is None


def test_remember_saves_the_fact(store):
    reply = _reply(make_memory_handler(store), "Запомни, что меня зовут Иван")
    assert reply.text == "Запомнила."
    assert reply.spoken is True
    assert store.facts() == ["меня зовут Иван"]


def test_remember_duplicate(store):
    handle = make_memory_handler(store)
    _reply(handle, "Запомни, что я люблю кофе")
    reply = _reply(handle, "запомни что я люблю кофе")
    assert reply.text == "Это я уже знаю."
    assert len(store) == 1


def test_remember_empty_asks_what(store):
    reply = _reply(make_memory_handler(store), "Запомни.")
    assert reply.text == "Что именно запомнить?"
    assert len(store) == 0


def test_remember_too_long(tmp_path):
    small = MemoryStore(tmp_path / "facts.json", max_fact_length=10)
    reply = _reply(make_memory_handler(small), "Запомни, что это очень длинный факт")
    assert reply.text == "Слишком длинно, скажи покороче."
    assert len(small) == 0


def test_remember_when_full(tmp_path):
    small = MemoryStore(tmp_path / "facts.json", max_facts=1)
    handle = make_memory_handler(small)
    _reply(handle, "Запомни, что я живу в Минске")
    reply = _reply(handle, "Запомни, что у меня есть кошка")
    assert reply.text == "Память заполнена. Сначала попроси что-нибудь забыть."
    assert len(small) == 1


def test_forget_one_fact(store):
    store.add("у меня есть кошка")
    reply = _reply(make_memory_handler(store), "Забудь про кошку")
    assert reply.text == "Забыла: у меня есть кошка"
    assert reply.spoken is True
    assert len(store) == 0


def test_forget_nothing_found(store):
    store.add("я живу в Минске")
    reply = _reply(make_memory_handler(store), "Забудь про кошку")
    assert reply.text == "Не нашла такого в памяти."
    assert len(store) == 1


def test_forget_empty_asks_what(store):
    store.add("я живу в Минске")
    reply = _reply(make_memory_handler(store), "Забудь.")
    assert reply.text == "Что именно забыть?"
    assert len(store) == 1


def test_forget_everything_does_not_wipe_memory(store):
    store.add("я всегда пью чай")
    reply = _reply(make_memory_handler(store), "Забудь всё")
    assert reply.text == "Что именно забыть?"
    assert len(store) == 1


def test_forget_many_facts_is_not_listed(store):
    for fact in (
        "люблю кофе утром",
        "кофе без сахара",
        "кофе пью из синей кружки",
        "кофе в офисе невкусный",
    ):
        store.add(fact)
    reply = _reply(make_memory_handler(store), "Забудь про кофе")
    assert reply.text == "Забыла несколько фактов."
    assert len(store) == 0


def test_recall_empty(store):
    reply = _reply(make_memory_handler(store), "Что ты обо мне помнишь?")
    assert reply.text == "Пока ничего о тебе не помню."
    assert reply.spoken is True


def test_recall_lists_facts(store):
    store.add("меня зовут Иван")
    store.add("я живу в Минске")
    reply = _reply(make_memory_handler(store), "Что ты обо мне помнишь?")
    assert reply.text == "Я помню: меня зовут Иван; я живу в Минске."


def test_recall_many_facts_speaks_only_first_five(store):
    for number in range(1, 8):
        store.add(f"факт номер {number}")
    reply = _reply(make_memory_handler(store), "Что ты обо мне помнишь?")
    assert "факт номер 5" in reply.text
    assert "факт номер 6" not in reply.text
    assert reply.text.endswith("И ещё 2.")


class BrokenStore:
    def add(self, text: str) -> AddStatus:
        raise RuntimeError("disk is gone")

    def forget(self, query: str) -> list[str]:
        raise RuntimeError("disk is gone")

    def facts(self) -> list[str]:
        raise RuntimeError("disk is gone")


@pytest.mark.parametrize(
    "phrase",
    ["Запомни, что я люблю чай", "Забудь про чай", "Что ты обо мне помнишь?"],
)
def test_broken_store_still_answers(phrase):
    reply = _reply(make_memory_handler(BrokenStore()), phrase)
    assert reply.text == "Что-то пошло не так с памятью."
    assert reply.spoken is True


def test_fact_text_is_not_logged(store, caplog):
    caplog.set_level("DEBUG")
    make_memory_handler(store)("Запомни, что мой секрет — зелёный жираф")
    assert "жираф" not in caplog.text
