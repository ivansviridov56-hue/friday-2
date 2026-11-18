import pytest

from friday.artist_request import parse_artist_request


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("включи исполнителя Киркорова", "Киркорова"),
        ("Пятница, поставь артиста Eminem", "Eminem"),
        ("включи мне группу Ленинград.", "Ленинград"),
        ("включи эту группу «Ленинград»", "Ленинград"),
        ("включи, пожалуйста, исполнителя Филипп Киркоров", "Филипп Киркоров"),
    ],
)
def test_artist_request_returns_query(text, expected):
    assert parse_artist_request(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "включи исполнителя",
        "включи песню Полетели",
        "включи свет",
        "расскажи про исполнителя Киркоров",
        "включи исполнителя один два три четыре пять шесть",
    ],
)
def test_not_an_artist_request(text):
    assert parse_artist_request(text) is None
