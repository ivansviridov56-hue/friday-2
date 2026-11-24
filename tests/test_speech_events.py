from friday.speech_events import make_chunk_publisher
from friday.ui_events import SpeechChunkStarted, UiEventBus


def test_chunk_is_published_on_the_bus():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    make_chunk_publisher(bus)("Hello there.", 1.5)
    assert got == [SpeechChunkStarted("Hello there.", 1.5)]
