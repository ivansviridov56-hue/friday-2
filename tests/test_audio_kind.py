from friday.audio import audio_kind


def test_wav_is_recognized_by_its_header() -> None:
    assert audio_kind(b"RIFF\x24\x00\x00\x00WAVEfmt ") == "wav"


def test_everything_else_is_treated_as_mp3() -> None:
    assert audio_kind(b"ID3\x03\x00") == "mp3"
    assert audio_kind(b"\xff\xfb\x90\x00") == "mp3"
    assert audio_kind(b"") == "mp3"
