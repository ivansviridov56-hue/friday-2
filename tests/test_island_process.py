import io
import subprocess
import base64

from friday.island_process import IslandProcess


class FakeStdin:
    def __init__(self, fail: bool = False) -> None:
        self.lines: list[str] = []
        self.closed = False
        self.fail = fail

    def write(self, text: str) -> None:
        if self.fail:
            raise BrokenPipeError
        self.lines.append(text)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class FakeProc:
    def __init__(
        self,
        output: str = "ready\n",
        returncode=None,
        hang: bool = False,
        fail_write: bool = False,
    ) -> None:
        self.stdin = FakeStdin(fail_write)
        self.stdout = io.StringIO(output)
        self.returncode = returncode
        self.hang = hang
        self.terminated = False

    def poll(self):
        return self.returncode

    def wait(self, timeout: float = 0.0):
        if self.hang and not self.terminated:
            raise subprocess.TimeoutExpired("island", timeout)
        self.returncode = 0
        return 0

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9


def make(proc: FakeProc) -> IslandProcess:
    return IslandProcess(spawn=lambda: proc)


def test_start_succeeds_on_ready():
    island = make(FakeProc())
    assert island.start() is True
    assert island.is_running


def test_start_fails_when_spawn_raises():
    def boom():
        raise OSError("no python")

    island = IslandProcess(spawn=boom)
    assert island.start() is False
    assert not island.is_running


def test_start_fails_when_process_ends_without_ready():
    island = make(FakeProc(output="", returncode=1))
    assert island.start() is False
    assert not island.is_running


def test_set_state_writes_a_line():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.set_state("listening")
    assert proc.stdin.lines == ["state listening\n"]


def test_set_state_before_start_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.set_state("listening")
    assert proc.stdin.lines == []


def test_non_string_state_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.set_state(None)  # type: ignore[arg-type]
    assert proc.stdin.lines == []


def test_state_with_whitespace_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.set_state("quit\nstate x")
    assert proc.stdin.lines == []


def test_stop_sends_quit_and_closes_stdin():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.stop()
    assert proc.stdin.lines == ["quit\n"]
    assert proc.stdin.closed
    assert not island.is_running


def test_stop_terminates_a_hanging_process():
    proc = FakeProc(hang=True)
    island = make(proc)
    island.start()
    island.stop()
    assert proc.terminated


def test_broken_pipe_marks_the_island_not_running():
    proc = FakeProc(fail_write=True)
    island = make(proc)
    island.start()
    island.set_state("idle")
    assert not island.is_running


def test_stop_without_start_is_safe():
    IslandProcess(spawn=lambda: FakeProc()).stop()


def test_set_state_after_stop_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.stop()
    island.set_state("idle")
    assert proc.stdin.lines == ["quit\n"]


def test_set_theme_writes_a_line():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.set_theme("windows")
    assert proc.stdin.lines == ["theme windows\n"]


def test_set_theme_before_start_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.set_theme("windows")
    assert proc.stdin.lines == []


def test_theme_with_whitespace_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.set_theme("windows\nquit")
    assert proc.stdin.lines == []


def test_show_text_sends_decodable_base64():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.show_text("Привет\nмир")
    line = proc.stdin.lines[0]
    assert line.startswith("text ") and line.endswith("\n")
    assert base64.b64decode(line[5:-1]).decode("utf-8") == "Привет\nмир"


def test_empty_text_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.show_text("   ")
    assert proc.stdin.lines == []


def test_show_text_before_start_is_ignored():
    proc = FakeProc()
    island = make(proc)
    island.show_text("привет")
    assert proc.stdin.lines == []


def test_clear_text_writes_a_line():
    proc = FakeProc()
    island = make(proc)
    island.start()
    island.clear_text()
    assert proc.stdin.lines == ["clear\n"]
