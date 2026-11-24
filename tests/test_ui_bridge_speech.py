import logging

from friday.ui_bridge import UiBridge
from friday.ui_events import SpeechChunkStarted


def test_speech_chunk_is_ignored_without_warning(caplog):
    calls = []
    bridge = UiBridge(calls.append)
    bridge.mark_ready()
    with caplog.at_level(logging.WARNING):
        bridge.on_event(SpeechChunkStarted("Hello.", 1.0))
    assert calls == []
    assert "unknown UI event" not in caplog.text
