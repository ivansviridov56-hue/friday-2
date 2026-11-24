from friday.ui_events import MessageAdded, SpeechChunkStarted, UiEventBus


def test_message_is_spoken_by_default():
    assert MessageAdded("assistant", "hi").spoken is True


def test_message_can_be_marked_as_not_spoken():
    assert MessageAdded("assistant", "hi", spoken=False).spoken is False


def test_speech_chunk_reaches_subscribers():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    bus.publish(SpeechChunkStarted("Hello there.", 1.5))
    assert got == [SpeechChunkStarted("Hello there.", 1.5)]


def test_speech_chunk_is_not_replayed_to_a_late_subscriber():
    bus = UiEventBus()
    bus.publish(SpeechChunkStarted("Hello there.", 1.5))
    late = []
    bus.subscribe(late.append)
    assert late == []
