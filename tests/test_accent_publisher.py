import logging

from friday.accent_publisher import AccentPublisher
from friday.ui_events import AccentChanged, UiEventBus


def palette(*colors):
    return b"".join(bytes(c) + b"\x00" for c in colors)


BEIGE = palette((0xEB, 0xDE, 0xBE), (0xD0, 0xBD, 0x9E))
BLUE = palette((0x99, 0xEB, 0xFF), (0x4C, 0xC2, 0xFF))


class FakeSource:
    def __init__(self, data):
        self.data = data

    def palette(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


def make(data):
    bus = UiEventBus()
    events = []
    bus.subscribe(events.append)
    source = FakeSource(data)
    return AccentPublisher(bus, source), source, events


def test_publishes_the_accent():
    publisher, _, events = make(BEIGE)
    publisher.poll_once()
    assert events == [AccentChanged("#d0bd9e", "#ebdebe")]


def test_does_not_repeat_an_unchanged_accent():
    publisher, _, events = make(BEIGE)
    publisher.poll_once()
    publisher.poll_once()
    assert len(events) == 1


def test_publishes_again_when_the_accent_changes():
    publisher, source, events = make(BEIGE)
    publisher.poll_once()
    source.data = BLUE
    publisher.poll_once()
    assert events[-1] == AccentChanged("#4cc2ff", "#99ebff")
    assert len(events) == 2


def test_missing_palette_publishes_nothing():
    publisher, _, events = make(None)
    publisher.poll_once()
    assert events == []


def test_broken_palette_is_logged_once_and_survived(caplog):
    publisher, _, events = make(b"\x00\x01")
    with caplog.at_level(logging.ERROR):
        publisher.poll_once()
        publisher.poll_once()
    assert events == []
    assert len(caplog.records) == 1


def test_recovers_after_a_failure():
    publisher, source, events = make(b"\x00\x01")
    publisher.poll_once()
    source.data = BEIGE
    publisher.poll_once()
    assert events == [AccentChanged("#d0bd9e", "#ebdebe")]
