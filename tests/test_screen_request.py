import pytest

from friday.screen_request import is_screen_request


@pytest.mark.parametrize(
    "text",
    [
        "Что на экране?",
        "Что у меня на экране",
        "Что сейчас на экране",
        "Пятница, что на экране?",
        "Что на экране, пожалуйста",
        "Посмотри на экран",
        "Посмотри на экран, пожалуйста",
        "Опиши экран",
        "Опиши, что на экране",
        "Скажи, что у меня на экране",
        "А что на экране?",
        "Ну опиши мне экран",
    ],
)
def test_screen_requests_are_recognized(text: str) -> None:
    assert is_screen_request(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Выключи экран",
        "Сделай экран ярче",
        "Что такое экран",
        "Что случилось с экраном",
        "Запомни, что на экране красный фон",
        "Что на экране телефона у моей мамы вчера было",
        "Включи свет",
        "Что ты обо мне помнишь",
        "Посмотри на меня",
        "Опиши картинку",
        "",
    ],
)
def test_other_phrases_are_not_screen_requests(text: str) -> None:
    assert is_screen_request(text) is False
