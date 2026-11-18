"""Tests for the long-term memory store (stage 8a)."""

import json
from pathlib import Path

import pytest

from friday.memory_store import AddStatus, MemoryStore


@pytest.fixture
def path(tmp_path: Path) -> Path:
    return tmp_path / "memory" / "facts.json"


def test_new_store_is_empty(path: Path) -> None:
    assert MemoryStore(path).facts() == []


def test_missing_file_is_not_created_until_first_add(path: Path) -> None:
    MemoryStore(path)
    assert not path.exists()


def test_add_returns_added_and_stores_the_fact(path: Path) -> None:
    store = MemoryStore(path)
    assert store.add("Меня зовут Иван") is AddStatus.ADDED
    assert store.facts() == ["Меня зовут Иван"]


def test_add_strips_surrounding_spaces(path: Path) -> None:
    store = MemoryStore(path)
    store.add("   люблю кофе  ")
    assert store.facts() == ["люблю кофе"]


def test_add_keeps_order(path: Path) -> None:
    store = MemoryStore(path)
    store.add("первое")
    store.add("второе")
    assert store.facts() == ["первое", "второе"]


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_add_rejects_empty_text(path: Path, text: str) -> None:
    store = MemoryStore(path)
    assert store.add(text) is AddStatus.EMPTY
    assert store.facts() == []


def test_add_rejects_duplicate_ignoring_case_yo_and_spaces(path: Path) -> None:
    store = MemoryStore(path)
    store.add("Мой ёж  зовётся Колючка")
    assert store.add("мой еж зовется колючка") is AddStatus.DUPLICATE
    assert len(store.facts()) == 1


def test_add_rejects_too_long_fact(path: Path) -> None:
    store = MemoryStore(path, max_fact_length=10)
    assert store.add("a" * 11) is AddStatus.TOO_LONG
    assert store.facts() == []


def test_add_accepts_fact_of_exact_max_length(path: Path) -> None:
    store = MemoryStore(path, max_fact_length=10)
    assert store.add("a" * 10) is AddStatus.ADDED


def test_add_rejects_when_full(path: Path) -> None:
    store = MemoryStore(path, max_facts=2)
    store.add("один")
    store.add("два")
    assert store.add("три") is AddStatus.FULL
    assert store.facts() == ["один", "два"]


def test_facts_returns_a_copy(path: Path) -> None:
    store = MemoryStore(path)
    store.add("факт")
    store.facts().append("чужой")
    assert store.facts() == ["факт"]


def test_facts_are_saved_and_loaded_by_a_new_store(path: Path) -> None:
    MemoryStore(path).add("живу в Минске")
    assert MemoryStore(path).facts() == ["живу в Минске"]


def test_file_is_utf8_json_with_readable_russian(path: Path) -> None:
    MemoryStore(path).add("кошка Муся")
    raw = path.read_text(encoding="utf-8")
    assert "кошка Муся" in raw
    assert json.loads(raw)["facts"] == ["кошка Муся"]


def test_save_creates_missing_parent_folders(path: Path) -> None:
    MemoryStore(path).add("факт")
    assert path.parent.is_dir()


def test_save_leaves_no_temporary_files(path: Path) -> None:
    MemoryStore(path).add("факт")
    assert [p.name for p in path.parent.iterdir()] == ["facts.json"]


def test_forget_removes_matching_facts_and_returns_them(path: Path) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    store.add("кошка Муся")
    removed = store.forget("кофе")
    assert removed == ["люблю кофе"]
    assert store.facts() == ["кошка Муся"]


def test_forget_removes_all_matches(path: Path) -> None:
    store = MemoryStore(path)
    store.add("кошка Муся")
    store.add("у кошки голубые глаза")
    store.add("люблю чай")
    assert store.forget("кошк") == ["кошка Муся", "у кошки голубые глаза"]
    assert store.facts() == ["люблю чай"]


def test_forget_ignores_case_and_yo(path: Path) -> None:
    store = MemoryStore(path)
    store.add("Мой ёж")
    assert store.forget("МОЙ ЕЖ") == ["Мой ёж"]


def test_forget_with_no_match_changes_nothing(path: Path) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    assert store.forget("чай") == []
    assert store.facts() == ["люблю кофе"]


@pytest.mark.parametrize("query", ["", "   ", "..."])
def test_forget_with_empty_query_removes_nothing(path: Path, query: str) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    assert store.forget(query) == []
    assert store.facts() == ["люблю кофе"]


def test_forget_is_saved(path: Path) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    store.forget("кофе")
    assert MemoryStore(path).facts() == []


def test_can_add_again_after_forget(path: Path) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    store.forget("кофе")
    assert store.add("люблю кофе") is AddStatus.ADDED


def test_corrupt_file_gives_empty_store_and_keeps_a_backup(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    store = MemoryStore(path)
    assert store.facts() == []
    backups = [p for p in path.parent.iterdir() if p.name.startswith("facts.json.bad")]
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{not json"


def test_corrupt_file_does_not_block_new_facts(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.write_text("[]", encoding="utf-8")
    store = MemoryStore(path)
    assert store.add("новый факт") is AddStatus.ADDED
    assert MemoryStore(path).facts() == ["новый факт"]


def test_non_string_items_in_file_are_dropped(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"facts": ["ok", 5, None, "  ", "тоже ok"]}), encoding="utf-8"
    )
    assert MemoryStore(path).facts() == ["ok", "тоже ok"]


def test_empty_store_reports_zero_count(path: Path) -> None:
    assert len(MemoryStore(path)) == 0


def test_len_counts_facts(path: Path) -> None:
    store = MemoryStore(path)
    store.add("a")
    store.add("b")
    assert len(store) == 2


@pytest.mark.parametrize("query", ["кошку", "кошкой", "кошки", "кошка"])
def test_forget_matches_inflected_words(path: Path, query: str) -> None:
    store = MemoryStore(path)
    store.add("у меня есть кошка")
    assert store.forget(query) == ["у меня есть кошка"]


def test_forget_needs_every_query_word_to_match(path: Path) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    assert store.forget("люблю чай") == []
    assert store.facts() == ["люблю кофе"]


def test_forget_ignores_word_order(path: Path) -> None:
    store = MemoryStore(path)
    store.add("люблю кофе")
    assert store.forget("кофе люблю") == ["люблю кофе"]


def test_forget_matches_a_whole_phrase_with_endings(path: Path) -> None:
    store = MemoryStore(path)
    store.add("мой день рождения 5 мая")
    assert store.forget("моего дня рождения") == []  # "моего" is not "мой": stays safe
    assert store.forget("мой день рождения") == ["мой день рождения 5 мая"]


def test_forget_short_words_must_match_exactly(path: Path) -> None:
    store = MemoryStore(path)
    store.add("ежедневно пью воду")
    assert store.forget("еж") == []
    assert store.facts() == ["ежедневно пью воду"]


def test_forget_does_not_match_a_longer_unrelated_word(path: Path) -> None:
    store = MemoryStore(path)
    store.add("потерял кошелёк")  # "кошелек" shares only "кош" with "кошку"
    assert store.forget("кошку") == []
    assert store.facts() == ["потерял кошелёк"]
