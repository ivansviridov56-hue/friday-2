import asyncio

import pytest

from friday.tts import (
    TtsError,
    TtsSettings,
    clean_for_speech,
    speak_async,
    split_sentences,
    synthesize,
    split_for_speech,
)


class FakeCommunicate:
    def __init__(self, text, voice, rate, pitch):
        self.text = text

    async def stream(self):
        yield {"type": "WordBoundary", "offset": 0}
        if "fail" not in self.text:
            yield {"type": "audio", "data": self.text.encode()}


def test_default_settings_match_chosen_voice():
    settings = TtsSettings()
    assert settings.voice == "ru-RU-SvetlanaNeural" and settings.rate == "+30%"


def test_clean_for_speech_removes_markdown():
    assert clean_for_speech("**Привет**  `босс`") == "Привет босс"


def test_split_sentences():
    assert split_sentences("Привет, босс. Как дела? Отлично!") == [
        "Привет, босс.",
        "Как дела?",
        "Отлично!",
    ]


def test_split_sentences_without_punctuation():
    assert split_sentences("просто фраза") == ["просто фраза"]


def test_synthesize_keeps_only_audio_chunks():
    audio = asyncio.run(synthesize("Раз", communicate=FakeCommunicate))
    assert audio == "Раз".encode()


def test_synthesize_raises_when_no_audio():
    with pytest.raises(TtsError):
        asyncio.run(synthesize("fail", communicate=FakeCommunicate))


def test_speak_plays_sentences_in_order():
    played = []
    count = asyncio.run(
        speak_async("Раз. Два. Три.", played.append, communicate=FakeCommunicate)
    )
    assert count == 3
    assert played == ["Раз.".encode(), "Два.".encode(), "Три.".encode()]


def test_speak_skips_failed_sentence_and_continues():
    played = []
    count = asyncio.run(
        speak_async("Раз. fail. Три.", played.append, communicate=FakeCommunicate)
    )
    assert count == 2
    assert played == ["Раз.".encode(), "Три.".encode()]


def test_split_for_speech_keeps_short_sentences():
    assert split_for_speech("Привет, босс. Чем помочь?") == [
        "Привет, босс.",
        "Чем помочь?",
    ]


def test_split_for_speech_cuts_long_sentence_at_commas():
    text = "aaaa aaaa, bbbb bbbb, cccc cccc, dddd dddd."
    assert split_for_speech(text, first_max=10, max_len=12) == [
        "aaaa aaaa,",
        "bbbb bbbb,",
        "cccc cccc,",
        "dddd dddd.",
    ]


def test_split_for_speech_does_not_cut_without_commas():
    text = "а" * 100
    assert split_for_speech(text) == [text]


class SlowCommunicate:
    active = 0
    peak = 0

    def __init__(self, text, voice, rate, pitch):
        self.text = text

    async def stream(self):
        SlowCommunicate.active += 1
        SlowCommunicate.peak = max(SlowCommunicate.peak, SlowCommunicate.active)
        await asyncio.sleep(0.01)
        SlowCommunicate.active -= 1
        yield {"type": "audio", "data": self.text.encode()}


def test_parallel_synthesis_is_limited():
    SlowCommunicate.active = SlowCommunicate.peak = 0
    played = []
    count = asyncio.run(
        speak_async(
            "Раз. Два. Три. Четыре. Пять.", played.append, communicate=SlowCommunicate
        )
    )
    assert count == 5 and len(played) == 5
    assert SlowCommunicate.peak <= 2
