import pytest

from friday.wave_cards import (
    WaveCard,
    cards_from_names,
    parse_card,
    parse_wave_card_request,
    pick_card,
)


@pytest.mark.parametrize(
    "name, kind, title",
    [
        ("Моя волна по жанру Украинский рок", "genre", "Украинский рок"),
        (
            "Моя волна под занятие Тренироваться в ритме",
            "activity",
            "Тренироваться в ритме",
        ),
        ("Моя волна по характеру Любимое", "character", "Любимое"),
        ("Моя волна по настроению Здесь так красиво", "mood", "Здесь так красиво"),
        ("Моя волна по артисту ЕГОР КРИД", "artist", "ЕГОР КРИД"),
        ("Моя волна — треки исполнителя MACAN", "artist", "MACAN"),
        ("Моя волна Энергичный поп", "other", "Энергичный поп"),
        ("Моя\xa0волна по жанру Это поп!", "genre", "Это поп!"),
    ],
)
def test_parse_card_kinds(name, kind, title):
    card = parse_card(name)
    assert card is not None
    assert (card.kind, card.title) == (kind, title)


@pytest.mark.parametrize(
    "name",
    [
        "Моя волна",
        "Моя волна —",
        "Сингл Претендент На Убийство",
        "Настроить Мою\xa0волну",
        "Встряхнуть Мою\xa0волну",
        "Моя волнаXYZ",
        "",
    ],
)
def test_parse_card_rejects_non_waves(name):
    assert parse_card(name) is None


def test_cards_from_names_drops_non_waves_and_copies():
    names = [
        "Моя волна по жанру Это поп!",
        "Сингл Претендент На Убийство",
        "Моя волна по жанру Это поп!",
        "Встряхнуть Мою\xa0волну",
        "Моя волна Энергичный поп",
    ]
    cards = cards_from_names(names)
    assert [card.title for card in cards] == ["Это поп!", "Энергичный поп"]


@pytest.mark.parametrize(
    "phrase, expected",
    [
        ("включи волну Это поп", "это поп"),
        ("Пятница, включи волну украинский рок", "украинский рок"),
        ("включи мою волну украинский рок", "украинский рок"),
        ("запусти волну по жанру рок", "рок"),
        ("включи мою волну", None),
        ("включи волну", None),
        ("волна поп", None),
        ("включи песню Мираж", None),
        ("включи волну волну поп", None),
        ("включи волну " + "слово " * 8, None),
    ],
)
def test_parse_wave_card_request(phrase, expected):
    assert parse_wave_card_request(phrase) == expected


CARDS = cards_from_names(
    [
        "Моя волна по жанру Это поп!",
        "Моя волна Энергичный поп",
        "Моя волна по жанру Попасть в поп-рок",
        "Моя волна Энергичная русская поп-музыка",
        "Моя волна под занятие Тренироваться в ритме",
        "Моя волна по артисту ЕГОР КРИД",
        "Моя волна — треки исполнителя MACAN",
    ]
)


def _title(query):
    card = pick_card(query, CARDS)
    return card.title if card else None


def test_pick_exact_title():
    assert _title("это поп") == "Это поп!"
    assert _title("энергичный поп") == "Энергичный поп"


def test_pick_tolerates_endings():
    assert _title("тренировка") == "Тренироваться в ритме"


def test_pick_artist_by_name():
    assert _title("егор крид") == "ЕГОР КРИД"
    assert _title("macan") == "MACAN"


def test_pick_ignores_kind_words():
    assert _title("по жанру это поп") == "Это поп!"


def test_pick_best_of_several():
    # four cards contain "поп": the shorter title listed first wins
    assert _title("поп") == "Это поп!"


def test_tie_goes_to_the_card_listed_first():
    first = WaveCard("Моя волна Альфа бета", "other", "Альфа бета")
    second = WaveCard("Моя волна Альфа гамма", "other", "Альфа гамма")
    assert pick_card("альфа", [second, first]) is second
    assert pick_card("альфа", [first, second]) is first


def test_pick_needs_every_spoken_word():
    assert _title("поп джаз") is None


def test_pick_with_only_stop_words_or_no_cards():
    assert _title("по жанру") is None
    assert pick_card("поп", []) is None


def test_language_card_title_has_no_marker():
    from friday.wave_cards import parse_card

    card = parse_card("Моя волна по языку Только на английском")
    assert card is not None
    assert (card.kind, card.title) == ("language", "Только на английском")


def test_song_and_band_requests_with_a_wave_word_are_not_cards():
    from friday.wave_cards import parse_wave_card_request

    for phrase in (
        "включи песню морская волна",
        "включи трек новая волна",
        "включи группу новая волна",
    ):
        assert parse_wave_card_request(phrase) is None, phrase


def test_artist_marker_after_the_wave_word_is_still_a_card_request():
    from friday.wave_cards import parse_wave_card_request

    assert parse_wave_card_request("включи волну артиста macan") == "macan"
