import pytest

from friday.history import ConversationHistory


def test_empty_history_returns_only_new_message() -> None:
    history = ConversationHistory()
    assert history.messages_with("привет") == [{"role": "user", "content": "привет"}]


def test_includes_previous_exchanges_in_order() -> None:
    history = ConversationHistory()
    history.add_exchange("q1", "a1")
    history.add_exchange("q2", "a2")
    assert history.messages_with("q3") == [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "q3"},
    ]


def test_messages_with_does_not_modify_history() -> None:
    history = ConversationHistory()
    history.messages_with("q1")
    assert len(history) == 0


def test_oldest_exchange_dropped_when_limit_exceeded() -> None:
    history = ConversationHistory(max_exchanges=2)
    for i in range(1, 4):
        history.add_exchange(f"q{i}", f"a{i}")
    contents = [m["content"] for m in history.messages_with("new")]
    assert contents == ["q2", "a2", "q3", "a3", "new"]


def test_clear_forgets_everything() -> None:
    history = ConversationHistory()
    history.add_exchange("q", "a")
    history.clear()
    assert len(history) == 0


def test_invalid_limit_rejected() -> None:
    with pytest.raises(ValueError):
        ConversationHistory(max_exchanges=0)
