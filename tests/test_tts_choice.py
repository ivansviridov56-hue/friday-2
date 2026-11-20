"""choose_tts: pick the voice engine by name."""

import pytest

from friday.tts_choice import choose_tts


class FakeVoice:
    def __init__(self) -> None:
        self.warmed = 0

    def synthesize(self, text: str) -> bytes:
        return b"RIFF" + text.encode()

    def warm_up(self) -> None:
        self.warmed += 1


@pytest.mark.parametrize("name", [None, "", "  ", "silero", " Silero "])
def test_silero_is_the_default_engine(name):
    voice = FakeVoice()
    choice = choose_tts(name, silero_factory=lambda: voice)
    assert choice.engine is not None
    assert choice.engine("a") == b"RIFFa"


def test_warm_up_warms_the_silero_voice():
    voice = FakeVoice()
    choice = choose_tts("silero", silero_factory=lambda: voice)
    choice.warm_up()
    assert voice.warmed == 1


def test_edge_has_no_engine_and_never_creates_silero():
    created = []
    choice = choose_tts("edge", silero_factory=lambda: created.append(1))
    assert choice.engine is None
    choice.warm_up()
    assert created == []


def test_edge_name_is_case_insensitive():
    assert choose_tts("EDGE", silero_factory=FakeVoice).engine is None


def test_unknown_name_fails_loudly():
    with pytest.raises(ValueError, match="TTS_ENGINE"):
        choose_tts("espeak", silero_factory=FakeVoice)
