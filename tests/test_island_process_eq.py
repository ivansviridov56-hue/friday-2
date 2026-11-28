from friday.island_process import IslandProcess


class _Stdin:
    def __init__(self):
        self.lines = []

    def write(self, line):
        self.lines.append(line)

    def flush(self):
        pass

    def close(self):
        pass


class _Proc:
    def __init__(self):
        self.stdin = _Stdin()
        self.stdout = ["ready\n"]

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0

    def terminate(self):
        pass

    def kill(self):
        pass


def test_set_eq_sends_one_line():
    proc = _Proc()
    island = IslandProcess(spawn=lambda: proc)
    assert island.start()
    island.set_eq([0, 0.5, 1])
    island.stop()
    assert "eq 0 50 100\n" in proc.stdin.lines


def test_set_eq_ignores_empty_levels():
    proc = _Proc()
    island = IslandProcess(spawn=lambda: proc)
    assert island.start()
    island.set_eq([])
    island.stop()
    assert not any(line.startswith("eq") for line in proc.stdin.lines)


def test_set_eq_is_ignored_when_not_running():
    IslandProcess(spawn=_Proc).set_eq([0.5, 0.5])
