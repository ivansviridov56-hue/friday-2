import pytest

from friday.music_commands import MusicCommand, parse_music_command

NOW = MusicCommand.NOW_PLAYING


@pytest.mark.parametrize(
    "text, expected",
    [
        ("стойграет", NOW),  # real log line: "что" + "играет" glued and smeared
        ("Стойграет.", NOW),
        ("чтоиграет", NOW),
        ("што играет", NOW),
        ("шо играет", NOW),
        ("сто играет", NOW),
        ("что играют", NOW),
        ("что йграет", NOW),
        ("следующаяпесня", MusicCommand.NEXT),
        ("включимузыку", MusicCommand.PLAY),
        ("поставьнапаузу", MusicCommand.PAUSE),
    ],
)
def test_mishearings_are_recognized(text, expected):
    assert parse_music_command(text) is expected


@pytest.mark.parametrize(
    "text",
    [
        "во что играем сегодня",
        "он играет на гитаре",
        "сто рублей",
        "сто песен",
        "здравствуйте",
        "спасибо",
        "музыкант",
        "включение",
        "воспроизведение",
        "плейлист",
        "стоп",
        "заиграет",
    ],
)
def test_lookalikes_are_not_commands(text):
    assert parse_music_command(text) is None
