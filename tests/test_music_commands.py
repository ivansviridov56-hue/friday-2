import pytest

from friday.music_commands import MusicCommand, parse_music_command

PAUSE = MusicCommand.PAUSE
PLAY = MusicCommand.PLAY
NEXT = MusicCommand.NEXT
PREVIOUS = MusicCommand.PREVIOUS
NOW = MusicCommand.NOW_PLAYING


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Пауза.", PAUSE),
        ("поставь на паузу", PAUSE),
        ("Поставь музыку на паузу", PAUSE),
        ("останови музыку", PAUSE),
        ("выключи музыку", PAUSE),
        ("Пятница, пожалуйста, поставь на паузу", PAUSE),
        ("включи музыку", PLAY),
        ("продолжи воспроизведение музыки", PLAY),
        ("Включи Яндекс Музик", PLAY),  # how Whisper may spell it
        ("пожалуйста включи музыку", PLAY),
        ("следующий трек", NEXT),
        ("Включи следующую песню", NEXT),
        ("переключи песню", NEXT),
        ("пропусти трек", NEXT),
        ("предыдущий трек", PREVIOUS),
        ("верни прошлую песню", PREVIOUS),
        ("включи предыдущий трек", PREVIOUS),
        ("что играет", NOW),
        ("Что сейчас играет?", NOW),
        ("как называется эта песня", NOW),
        ("что за песня играет", NOW),
        ("кто поёт", NOW),
    ],
)
def test_music_commands_are_recognized(text, expected):
    assert parse_music_command(text) is expected


@pytest.mark.parametrize(
    "text",
    [
        "привет как дела",
        "расскажи про следующий шаг",
        "продолжай рассказ",
        "что ты думаешь про эту песню",
        "включи песню группа крови сектор газа",
        "включи песню группа крови",
        "пауза в разговоре затянулась давай уже что-нибудь решим наконец",
        "",
        "   ",
    ],
)
def test_ordinary_speech_is_not_a_command(text):
    assert parse_music_command(text) is None
