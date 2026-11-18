import numpy as np

from friday.recorder import Recorder


class FakeStream:
    def __init__(self, callback) -> None:
        self.callback = callback
        self.started = False
        self.closed = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False

    def close(self) -> None:
        self.closed = True

    def feed(self, samples: np.ndarray) -> None:
        self.callback(samples.reshape(-1, 1), len(samples), None, None)


def make_recorder() -> tuple[Recorder, list[FakeStream]]:
    streams: list[FakeStream] = []

    def factory(samplerate, channels, dtype, callback) -> FakeStream:
        stream = FakeStream(callback)
        streams.append(stream)
        return stream

    return Recorder(stream_factory=factory), streams


def ones(n: int) -> np.ndarray:
    return np.ones(n, dtype=np.float32)


def test_open_starts_stream_once() -> None:
    rec, streams = make_recorder()
    rec.open()
    rec.open()
    assert len(streams) == 1 and streams[0].started and rec.is_open


def test_audio_before_start_is_discarded() -> None:
    rec, streams = make_recorder()
    rec.open()
    streams[0].feed(ones(100))
    rec.start()
    streams[0].feed(ones(50))
    assert rec.stop().shape == (50,)


def test_stop_returns_concatenated_mono_float32() -> None:
    rec, streams = make_recorder()
    rec.open()
    rec.start()
    streams[0].feed(ones(100))
    streams[0].feed(np.full(50, 2.0, dtype=np.float32))
    audio = rec.stop()
    assert audio.dtype == np.float32
    assert audio.shape == (150,)
    assert audio[0] == 1.0 and audio[-1] == 2.0


def test_stop_without_chunks_returns_empty() -> None:
    rec, _ = make_recorder()
    rec.open()
    rec.start()
    assert rec.stop().size == 0


def test_stop_without_start_returns_empty() -> None:
    rec, streams = make_recorder()
    assert rec.stop().size == 0
    rec.open()
    streams[0].feed(ones(10))
    assert rec.stop().size == 0


def test_start_twice_keeps_one_recording() -> None:
    rec, streams = make_recorder()
    rec.open()
    rec.start()
    streams[0].feed(ones(10))
    rec.start()
    streams[0].feed(ones(10))
    assert rec.stop().size == 20 and len(streams) == 1


def test_stream_stays_open_between_recordings() -> None:
    rec, streams = make_recorder()
    rec.open()
    rec.start()
    streams[0].feed(ones(10))
    rec.stop()
    assert rec.is_open and not rec.is_recording and not streams[0].closed
    rec.start()
    assert rec.stop().size == 0  # nothing left over from the first recording


def test_audio_between_recordings_is_discarded() -> None:
    rec, streams = make_recorder()
    rec.open()
    rec.start()
    rec.stop()
    streams[0].feed(ones(100))
    rec.start()
    streams[0].feed(ones(5))
    assert rec.stop().size == 5


def test_start_opens_stream_lazily() -> None:
    rec, streams = make_recorder()
    rec.start()
    assert len(streams) == 1 and rec.is_open and rec.is_recording


def test_close_closes_stream_and_stops_recording() -> None:
    rec, streams = make_recorder()
    rec.start()
    rec.close()
    assert streams[0].closed and not rec.is_open and not rec.is_recording


def test_close_without_open_is_safe() -> None:
    rec, _ = make_recorder()
    rec.close()


def test_listener_gets_frames_without_recording() -> None:
    rec, streams = make_recorder()
    rec.open()
    heard: list[np.ndarray] = []
    rec.add_listener(heard.append)
    streams[0].feed(ones(10))
    streams[0].feed(ones(5))
    assert [f.shape for f in heard] == [(10,), (5,)]
    assert heard[0].dtype == np.float32
    assert rec.stop().size == 0  # listening is not recording


def test_listener_does_not_disturb_push_to_talk_recording() -> None:
    rec, streams = make_recorder()
    rec.open()
    heard: list[np.ndarray] = []
    rec.add_listener(heard.append)
    rec.start()
    streams[0].feed(ones(10))
    assert len(heard) == 1
    assert rec.stop().shape == (10,)


def test_removed_listener_gets_nothing_more() -> None:
    rec, streams = make_recorder()
    rec.open()
    heard: list[np.ndarray] = []
    rec.add_listener(heard.append)
    streams[0].feed(ones(10))
    rec.remove_listener(heard.append)
    streams[0].feed(ones(10))
    assert len(heard) == 1


def test_same_listener_added_twice_is_called_once() -> None:
    rec, streams = make_recorder()
    rec.open()
    calls: list[int] = []

    def listener(frame: np.ndarray) -> None:
        calls.append(frame.size)

    rec.add_listener(listener)
    rec.add_listener(listener)
    streams[0].feed(ones(10))
    assert calls == [10]


def test_broken_listener_breaks_neither_recording_nor_other_listeners() -> None:
    rec, streams = make_recorder()
    rec.open()
    heard: list[np.ndarray] = []

    def broken(frame: np.ndarray) -> None:
        raise RuntimeError("boom")

    rec.add_listener(broken)
    rec.add_listener(heard.append)
    rec.start()
    streams[0].feed(ones(10))
    assert len(heard) == 1
    assert rec.stop().shape == (10,)


def test_removing_an_unknown_listener_is_safe() -> None:
    rec, _ = make_recorder()
    rec.remove_listener(lambda frame: None)
