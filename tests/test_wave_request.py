import pytest

from friday.wave_request import is_wave_request, parse_wave_mood


@pytest.mark.parametrize(
    "text",
    [
        "Включи мою волну",
        "Пятница, запусти мою волну",
        "Включи мою волну, пожалуйста",
        "Поставь мою волну",
        "Моя волна",
        "Включи Мою Волну!",
    ],
)
def test_wave_request_is_recognized(text: str) -> None:
    assert is_wave_request(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Включи волну",
        "Включи мою музыку",
        "Что такое моя волна",
        "Расскажи про мою волну",
        "Моя волна мне нравится",
        "Включи мою волну по настроению",
        "Включи мою волну для тренировки",
        "Включи мою волну, спокойное",
        "Включи мою веселую волну",
    ],
)
def test_other_phrases_are_not_wave_requests(text: str) -> None:
    assert not is_wave_request(text)


@pytest.mark.parametrize(
    ("text", "mood"),
    [
        ("Включи мою волну, спокойное", "calm"),
        ("Пятница, включи мою волну бодрое", "active"),
        ("Включи мою веселую волну", "fun"),
        ("Включи мою весёлую волну", "fun"),
        ("Запусти мою грустную волну", "sad"),
        ("Включи мою волну по настроению грустное", "sad"),
        ("Поставь мою волну на спокойное, пожалуйста", "calm"),
    ],
)
def test_wave_mood_is_recognized(text: str, mood: str) -> None:
    assert parse_wave_mood(text) == mood


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Включи мою волну",
        "Включи мою волну по настроению",
        "Включи мою волну для тренировки",
        "Включи спокойную музыку",
        "Включи волну спокойное",
        "Расскажи про мою спокойную волну",
        "Что такое моя веселая волна",
        "Включи мою волну спокойное или веселое",
    ],
)
def test_wave_mood_is_not_recognized(text: str) -> None:
    assert parse_wave_mood(text) is None
