import base64

from friday.island_process import IslandProcess


class FakeStdin:
    def __init__(self):
        self.lines: list[str] = []

    def write(self, text):
        self.lines.append(text)

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
    return island, proc.stdin.lines


def test_reveal_sends_base64_text():
    island, lines = started()
    island.start_reveal("Привет, босс.")
    payload = base64.b64encode("Привет, босс.".encode("utf-8")).decode("ascii")
    assert lines == [f"reveal {payload}\n"]


def test_reveal_ignores_empty_text():
    island, lines = started()
    island.start_reveal("   ")
    assert lines == []


def test_chunk_sends_span_and_seconds():
    island, lines = started()
    island.reveal_chunk(13, 37, 1.25)
    assert lines == ["chunk 13 37 1.250\n"]


def test_chunk_with_bad_values_is_ignored():
    island, lines = started()
    for args in [
        (-1, 5, 1.0),
        (5, 3, 1.0),
        (0, 5, -1.0),
        (0, 5, float("nan")),
        (0, 5, float("inf")),
    ]:
        island.reveal_chunk(*args)
    assert lines == []


def test_reveal_and_chunk_are_ignored_when_not_running():
    proc = FakeProc()
    island = IslandProcess(spawn=lambda: proc)
    island.start_reveal("text")
    island.reveal_chunk(0, 4, 1.0)
    assert proc.stdin.lines == []


def test_finish_reveal_sends_done():
    island, lines = started()
    island.finish_reveal()
    assert lines == ["done\n"]


def test_finish_reveal_is_ignored_when_not_running():
    proc = FakeProc()
    island = IslandProcess(spawn=lambda: proc)
    island.finish_reveal()
    assert proc.stdin.lines == []
