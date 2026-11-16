import asyncio

from friday.tts_samples import VARIANTS, render_all, soften_punctuation


class FakeSpeaker:
    def __init__(self, text, voice, rate, pitch):
        self.voice = voice

    async def save(self, path):
        with open(path, "wb") as handle:
            handle.write(b"audio")


class BrokenSpeaker(FakeSpeaker):
    async def save(self, path):
        raise ConnectionError("no network")


def test_variant_names_are_unique():
    names = [v.name for v in VARIANTS]
    assert len(names) == len(set(names))


def test_render_all_writes_one_file_per_variant(tmp_path):
    results = asyncio.run(render_all(out_dir=tmp_path, communicate=FakeSpeaker))
    assert len(results) == len(VARIANTS)
    assert all((tmp_path / f"{v.name}.mp3").exists() for v in VARIANTS)


def test_render_all_reports_failures_without_raising(tmp_path):
    results = asyncio.run(render_all(out_dir=tmp_path, communicate=BrokenSpeaker))
    assert set(results.values()) == {"failed: ConnectionError"}


class HalfWrittenSpeaker(FakeSpeaker):
    async def save(self, path):
        with open(path, "wb"):
            pass
        raise ConnectionError("dropped")


def test_failed_render_leaves_no_empty_file(tmp_path):
    asyncio.run(render_all(out_dir=tmp_path, communicate=HalfWrittenSpeaker))
    assert list(tmp_path.iterdir()) == []


class RecordingSpeaker(FakeSpeaker):
    texts = []

    def __init__(self, text, voice, rate, pitch):
        super().__init__(text, voice, rate, pitch)
        RecordingSpeaker.texts.append(text)


def test_soften_punctuation_drops_commas_only():
    assert soften_punctuation("Привет, босс. Чем помочь?") == "Привет босс. Чем помочь?"


def test_soft_variant_sends_text_without_commas(tmp_path):
    RecordingSpeaker.texts = []
    asyncio.run(
        render_all(out_dir=tmp_path, phrase="Да, босс.", communicate=RecordingSpeaker)
    )
    assert "Да босс." in RecordingSpeaker.texts
    assert "Да, босс." in RecordingSpeaker.texts
