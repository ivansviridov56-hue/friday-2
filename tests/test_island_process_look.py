import pytest

from friday.island_process import IslandProcess


class FakeStdin:
    def __init__(self):
        self.lines = []

    def write(self, line):
        self.lines.append(line)

    def flush(self):
        pass

    def close(self):
        pass


class FakeProc:
    def __init__(self):
        self.stdin = FakeStdin()
        self.stdout = iter(["ready\n"])

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0

    def terminate(self):
        pass

    def kill(self):
        pass


def started():
    proc = FakeProc()
    island = IslandProcess(spawn=lambda: proc)
    assert island.start()
    return island, proc


def test_set_look_sends_the_look():
    island, proc = started()
    island.set_look("eyes")
    assert proc.stdin.lines == ["look eyes\n"]
    island.stop()


@pytest.mark.parametrize("bad", ["", "two words", None, 5])
def test_set_look_ignores_a_bad_value(bad):
    island, proc = started()
    island.set_look(bad)
    assert proc.stdin.lines == []
    island.stop()


def test_set_look_is_ignored_when_not_running():
    island = IslandProcess(spawn=lambda: FakeProc())
    island.set_look("eyes")
    assert not island.is_running
