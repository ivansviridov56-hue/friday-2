import pytest

from friday.wave_request import is_wave_request


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
    ],
)
def test_other_phrases_are_not_wave_requests(text: str) -> None:
    assert not is_wave_request(text)
