import numpy as np

from friday.turn_runner import TurnRunner


def inline(task) -> None:
    task()


def test_text_goes_to_the_handler_like_audio() -> None:
    got: list = []
    runner = TurnRunner(got.append, spawn=inline)
    assert runner.submit("включи свет") is True
    audio = np.zeros(3, dtype=np.float32)
    assert runner.submit(audio) is True
    assert got[0] == "включи свет" and got[1] is audio


def test_text_is_dropped_while_busy() -> None:
    got: list = []
    pending: list = []
    runner = TurnRunner(got.append, spawn=pending.append)
    assert runner.submit("первая") is True
    assert runner.is_busy
    assert runner.submit("вторая") is False
    pending[0]()
    assert got == ["первая"] and not runner.is_busy
