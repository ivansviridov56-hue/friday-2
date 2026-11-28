import pytest

from friday.eq_publisher import MAX_DT, EqPublisher


class FakeCapture:
    def __init__(self, ok=True):
        self.ok = ok
        self.rate = 48000
        self.channels = 2
        self.opened = False
        self.started = False
        self.closed = 0
        self.on_block = None

    def open(self):
        self.opened = True
        return self.ok

    def start(self, on_block):
        self.started = True
        self.on_block = on_block
        return True

    def close(self):
        self.closed += 1


class FakeEngine:
    def __init__(self, rate, channels):
        self.args = (rate, channels)
        self.fed = []
        self.dts = []

    def feed(self, raw):
        self.fed.append(raw)

    def levels(self, dt):
        self.dts.append(dt)
        return [0.5] * 16


class Rig:
    def __init__(self, ok=True):
        self.playing = False
        self.captures = []
        self.engines = []
        self.sent = []
        self.ok = ok
        self.publisher = EqPublisher(
            lambda: self.playing, self._capture, self._engine, self.sent.append
        )

    def _capture(self):
        capture = FakeCapture(self.ok)
        self.captures.append(capture)
        return capture

    def _engine(self, rate, channels):
        engine = FakeEngine(rate, channels)
        self.engines.append(engine)
        return engine


def test_nothing_happens_while_music_is_silent():
    rig = Rig()
    rig.publisher.step(0.0)
    rig.publisher.step(0.6)
    assert rig.captures == []
    assert rig.sent == []


def test_playing_starts_the_capture_and_sends_levels():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    assert len(rig.captures) == 1
    assert rig.captures[0].started
    assert rig.engines[0].args == (48000, 2)
    assert rig.sent == [[0.5] * 16]


def test_blocks_go_to_the_engine():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    rig.captures[0].on_block(b"abc")
    assert rig.engines[0].fed == [b"abc"]


def test_next_steps_keep_sending_with_the_real_time_step():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    rig.publisher.step(0.04)
    assert len(rig.sent) == 2
    assert rig.engines[0].dts[1] == pytest.approx(0.04)
    assert len(rig.captures) == 1


def test_a_long_gap_is_cut_to_the_maximum():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    rig.publisher.step(0.3)
    assert rig.engines[0].dts[1] == MAX_DT


def test_pause_closes_the_capture_and_stops_sending():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    rig.playing = False
    rig.publisher.step(0.6)
    assert rig.captures[0].closed == 1
    assert len(rig.sent) == 1
    rig.publisher.step(1.2)
    assert len(rig.sent) == 1


def test_play_again_opens_a_new_capture():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    rig.playing = False
    rig.publisher.step(0.6)
    rig.playing = True
    rig.publisher.step(1.2)
    assert len(rig.captures) == 2
    assert len(rig.engines) == 2


def test_a_failed_capture_is_retried_only_after_a_pause():
    rig = Rig(ok=False)
    rig.playing = True
    rig.publisher.step(0.0)
    rig.publisher.step(0.6)
    assert len(rig.captures) == 1
    assert rig.sent == []
    assert rig.captures[0].closed == 1
    rig.publisher.step(5.1)
    assert len(rig.captures) == 2


def test_a_failing_player_check_counts_as_silence():
    def broken():
        raise RuntimeError("boom")

    publisher = EqPublisher(broken, FakeCapture, FakeEngine, lambda levels: None)
    publisher.step(0.0)
    publisher.step(1.0)


def test_a_failing_sink_does_not_stop_the_loop():
    rig = Rig()
    rig.playing = True

    def broken(levels):
        raise OSError("pipe is gone")

    rig.publisher._sink = broken
    rig.publisher.step(0.0)
    rig.publisher.step(0.05)
    assert len(rig.engines[0].dts) == 2


def test_close_releases_the_capture():
    rig = Rig()
    rig.playing = True
    rig.publisher.step(0.0)
    rig.publisher.close()
    assert rig.captures[0].closed == 1
    rig.publisher.close()
    assert rig.captures[0].closed == 1
