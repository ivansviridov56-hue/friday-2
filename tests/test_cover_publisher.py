import time

from friday.cover_data import to_data_url
from friday.cover_publisher import CoverPublisher
from friday.ui_events import CoverChanged, StateChanged, State, UiEventBus

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
PNG2 = b"\x89PNG\r\n\x1a\n" + b"\x01" * 8


class FakeSource:
    def __init__(self):
        self.key_value: tuple[str, str] | None = None
        self.data: bytes | None = None
        self.cover_calls = 0
        self.fail = False

    def key(self):
        if self.fail:
            raise RuntimeError("boom")
        return self.key_value

    def cover(self):
        self.cover_calls += 1
        return self.data


def make():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    source = FakeSource()
    return bus, got, source, CoverPublisher(bus, source)


def test_nothing_playing_publishes_nothing():
    _, got, _, pub = make()
    pub.poll_once()
    assert got == []


def test_new_track_publishes_cover():
    _, got, source, pub = make()
    source.key_value, source.data = ("Song", "Artist"), PNG
    pub.poll_once()
    assert got == [CoverChanged(to_data_url(PNG))]


def test_same_track_does_not_fetch_again():
    _, got, source, pub = make()
    source.key_value, source.data = ("Song", "Artist"), PNG
    pub.poll_once()
    pub.poll_once()
    assert source.cover_calls == 1
    assert len(got) == 1


def test_track_change_publishes_new_cover():
    _, got, source, pub = make()
    source.key_value, source.data = ("One", "A"), PNG
    pub.poll_once()
    source.key_value, source.data = ("Two", "B"), PNG2
    pub.poll_once()
    assert got == [CoverChanged(to_data_url(PNG)), CoverChanged(to_data_url(PNG2))]


def test_music_closed_hides_the_circle():
    _, got, source, pub = make()
    source.key_value, source.data = ("Song", "Artist"), PNG
    pub.poll_once()
    source.key_value = None
    pub.poll_once()
    assert got[-1] == CoverChanged(None)


def test_missing_cover_is_retried_until_it_appears():
    _, got, source, pub = make()
    source.key_value, source.data = ("Song", "Artist"), None
    pub.poll_once()
    pub.poll_once()
    assert got == [CoverChanged(None)]
    assert source.cover_calls == 2
    source.data = PNG
    pub.poll_once()
    assert got[-1] == CoverChanged(to_data_url(PNG))


def test_source_error_does_not_raise_or_publish():
    _, got, source, pub = make()
    source.fail = True
    pub.poll_once()
    pub.poll_once()
    assert got == []


def test_start_publishes_and_close_stops():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    source = FakeSource()
    source.key_value, source.data = ("Song", "Artist"), PNG
    pub = CoverPublisher(bus, source, interval=0.01)
    pub.start()
    deadline = time.monotonic() + 2
    while not got and time.monotonic() < deadline:
        time.sleep(0.01)
    pub.close()
    assert got == [CoverChanged(to_data_url(PNG))]


def test_late_subscriber_gets_last_cover():
    bus = UiEventBus()
    bus.publish(CoverChanged("data:image/png;base64,AAA"))
    got = []
    bus.subscribe(got.append)
    assert got == [CoverChanged("data:image/png;base64,AAA")]


def test_late_subscriber_gets_no_cover_if_none_was_published():
    bus = UiEventBus()
    bus.publish(StateChanged(State.IDLE))
    got = []
    bus.subscribe(got.append)
    assert got == [StateChanged(State.IDLE)]


def test_late_subscriber_gets_only_the_latest_cover():
    bus = UiEventBus()
    bus.publish(CoverChanged("data:image/png;base64,AAA"))
    bus.publish(CoverChanged(None))
    got = []
    bus.subscribe(got.append)
    assert got == [CoverChanged(None)]
