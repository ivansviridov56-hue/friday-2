from friday.wallpaper_source import FileWallpaperSource
from friday.wallpaper_watcher import WallpaperWatcher


class FakeSource:
    def __init__(self, stamp):
        self.value = stamp
        self.fail = False

    def stamp(self):
        if self.fail:
            raise RuntimeError("boom")
        return self.value


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def make(source=None, clock=None):
    calls = []
    source = source or FakeSource(1)
    clock = clock or FakeClock()
    watcher = WallpaperWatcher(
        source, lambda: calls.append(1), min_gap=2.0, clock=clock
    )
    return watcher, source, clock, calls


def test_first_reading_is_not_a_change():
    watcher, _, _, calls = make()
    watcher.poll_once()
    assert calls == []


def test_no_change_no_signal():
    watcher, _, _, calls = make()
    watcher.poll_once()
    watcher.poll_once()
    assert calls == []


def test_change_gives_one_signal():
    watcher, source, _, calls = make()
    watcher.poll_once()
    source.value = 2
    watcher.poll_once()
    assert calls == [1]


def test_a_burst_gives_one_signal():
    watcher, source, clock, calls = make()
    watcher.poll_once()
    for value in (2, 3, 4):
        source.value = value
        clock.now += 0.05
        watcher.poll_once()
    assert calls == [1]


def test_next_change_after_the_gap_gives_a_new_signal():
    watcher, source, clock, calls = make()
    watcher.poll_once()
    source.value = 2
    watcher.poll_once()
    clock.now += 5.0
    source.value = 3
    watcher.poll_once()
    assert calls == [1, 1]


def test_a_burst_tail_is_not_a_late_signal():
    watcher, source, clock, calls = make()
    watcher.poll_once()
    source.value = 2
    watcher.poll_once()
    source.value = 3
    clock.now += 0.1
    watcher.poll_once()
    clock.now += 5.0
    watcher.poll_once()
    assert calls == [1]


def test_unreadable_file_does_not_crash_and_returns_later():
    watcher, source, clock, calls = make()
    watcher.poll_once()
    source.fail = True
    watcher.poll_once()
    watcher.poll_once()
    source.fail = False
    source.value = 2
    watcher.poll_once()
    assert calls == [1]


def test_file_source_reads_the_change_time(tmp_path):
    path = tmp_path / "wall"
    source = FileWallpaperSource(path)
    assert source.stamp() is None
    path.write_bytes(b"a")
    first = source.stamp()
    assert isinstance(first, int)


def test_file_source_without_a_path_gives_none(monkeypatch):
    monkeypatch.delenv("APPDATA", raising=False)
    assert FileWallpaperSource().stamp() is None
