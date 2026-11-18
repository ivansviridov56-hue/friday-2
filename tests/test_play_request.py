import pytest

from friday.play_request import parse_play_request


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("включи песню Полетели Киркоров", "Полетели Киркоров"),
        ("Пятница, поставь трек Till I Collapse Eminem", "Till I Collapse Eminem"),
        ("включи мне песню Полетели.", "Полетели"),
        ("Включи, пожалуйста, песню «Полетели»", "Полетели"),
        ("включи эту песню Полетели", "Полетели"),
        ("сыграй композицию Полетели Киркоров", "Полетели Киркоров"),
    ],
)
def test_play_request_returns_query(text, expected):
    assert parse_play_request(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "включи трек",
        "включи песню",
        "включи музыку",
        "включи свет",
        "поставь будильник",
        "что за песня",
        "расскажи про песню Полетели",
        "мне нравится песня Полетели",
        "включи песню один два три четыре пять шесть семь восемь девять",
    ],
)
def test_not_a_play_request(text):
    assert parse_play_request(text) is None
