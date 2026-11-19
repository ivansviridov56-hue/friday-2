import pytest

from friday.wake_word import contains_wake_word, split_wake_phrase


@pytest.mark.parametrize(
    "text",
    [
        "Пятница",
        "пятница!",
        "Слушай, Пятница, включи музыку",
        "Слушай пятницу, включи музыку.",
        "Ветница.",  # heard live: quiet voice, first letter lost
        "Пятенца.",  # heard live: normal voice
        "Эй, ветница, что на экране",
        "ПЯТНИЦА",
        "Включи музыку, Пятница.",
    ],
)
def test_name_and_heard_variants_are_found(text: str) -> None:
    assert contains_wake_word(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Бэтни",
        "Пятый",
        "Пять",
        "Пятно на рубашке",
        "Мне пятнадцать лет",
        "Пятка болит",
        "Сижу в пятом ряду",
        "Расскажи что-нибудь, как будто ассистента нет.",
        "Включи свет",
    ],
)
def test_other_words_are_not_the_name(text: str) -> None:
    assert contains_wake_word(text) is False


def test_stricter_threshold_can_be_passed() -> None:
    assert contains_wake_word("Ветница", threshold=0.9) is False
    assert contains_wake_word("Пятница", threshold=0.9) is True


@pytest.mark.parametrize(
    ("text", "rest"),
    [
        ("Пятница", ""),
        ("Пятница!", ""),
        ("Ветница.", ""),
        ("Пятница, что на экране?", "что на экране?"),
        ("Слушай, Пятница, включи музыку", "включи музыку"),
        ("Слушай пятницу, включи музыку.", "включи музыку."),
        ("Эй, пятенца, пауза", "пауза"),
        ("Ну слушай пятница включи свет", "включи свет"),
        ("привет пятница", ""),
    ],
)
def test_phrase_starting_with_the_name_is_split(text: str, rest: str) -> None:
    assert split_wake_phrase(text) == rest


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Слушай",
        "В пятницу поедем на дачу",
        "Сегодня пятница",
        "До пятницы осталось два дня",
        "Включи музыку, Пятница",
        "Ну ну слушай пятница",  # three lead-in words are too many
        "Пятый раз прошу",
        "Расскажи что-нибудь про пятницу",
        "Включи свет",
    ],
)
def test_name_not_at_the_start_is_not_a_wake_phrase(text: str) -> None:
    assert split_wake_phrase(text) is None
