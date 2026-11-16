import threading

import numpy as np

from friday.turn_runner import TurnRunner

AUDIO = np.ones(10, dtype=np.float32)


class ManualSpawn:
    """Collects tasks so a test decides when they run."""

    def __init__(self) -> None:
        self.tasks: list = []

    def __call__(self, task) -> None:
        self.tasks.append(task)

    def run_all(self) -> None:
        tasks, self.tasks = self.tasks, []
        for task in tasks:
            task()


def test_submit_hands_audio_to_handler_via_spawn() -> None:
    heard: list = []
    spawn = ManualSpawn()
    runner = TurnRunner(heard.append, spawn=spawn)
    assert runner.submit(AUDIO) is True
    assert heard == [] and runner.is_busy
    spawn.run_all()
    assert heard == [AUDIO] and not runner.is_busy


def test_submit_while_busy_is_ignored() -> None:
    heard: list = []
    spawn = ManualSpawn()
    runner = TurnRunner(heard.append, spawn=spawn)
    assert runner.submit(AUDIO) is True
    assert runner.submit(AUDIO) is False
    spawn.run_all()
    assert len(heard) == 1


def test_can_submit_again_after_turn_finishes() -> None:
    heard: list = []
    spawn = ManualSpawn()
    runner = TurnRunner(heard.append, spawn=spawn)
    runner.submit(AUDIO)
    spawn.run_all()
    assert runner.submit(AUDIO) is True
    spawn.run_all()
    assert len(heard) == 2


def test_handler_error_does_not_leave_runner_busy() -> None:
    def bad(audio) -> None:
        raise RuntimeError("boom")

    spawn = ManualSpawn()
    runner = TurnRunner(bad, spawn=spawn)
    runner.submit(AUDIO)
    spawn.run_all()
    assert not runner.is_busy
    assert runner.submit(AUDIO) is True


def test_spawn_failure_does_not_leave_runner_busy() -> None:
    def broken_spawn(task) -> None:
        raise RuntimeError("cannot start thread")

    runner = TurnRunner(lambda audio: None, spawn=broken_spawn)
    assert runner.submit(AUDIO) is False
    assert not runner.is_busy


def test_default_spawn_runs_handler_in_another_thread() -> None:
    done = threading.Event()
    thread_names: list[str] = []

    def handler(audio) -> None:
        thread_names.append(threading.current_thread().name)
        done.set()

    runner = TurnRunner(handler)
    runner.submit(AUDIO)
    assert done.wait(timeout=5)
    assert thread_names != [threading.current_thread().name]
