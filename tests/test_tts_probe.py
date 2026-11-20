import asyncio

import pytest

from friday.tts_probe import Outcome, run_round, summarize


def make_synth(delay: float = 0.005):
    state = {"active": 0, "peak": 0}

    async def synth(text: str) -> bytes:
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        await asyncio.sleep(delay)
        state["active"] -= 1
        return b"x"

    return synth, state


def test_round_respects_the_parallel_limit() -> None:
    synth, state = make_synth()
    outcomes = asyncio.run(run_round(["a"] * 6, synth, parallel=2))
    assert len(outcomes) == 6 and all(o.ok for o in outcomes)
    assert state["peak"] == 2


def test_round_can_go_one_at_a_time() -> None:
    synth, state = make_synth()
    asyncio.run(run_round(["a"] * 4, synth, parallel=1))
    assert state["peak"] == 1


def test_failure_is_recorded_not_raised() -> None:
    async def synth(text: str) -> bytes:
        if text == "bad":
            raise ConnectionError("dropped")
        return b"x"

    outcomes = asyncio.run(run_round(["ok", "bad"], synth, parallel=1))
    assert [o.ok for o in outcomes] == [True, False]
    assert outcomes[1].error == "ConnectionError"
    assert outcomes[1].text == "bad"


def test_summary_counts_failures_and_times() -> None:
    text = summarize(
        [
            Outcome("a", True, 100),
            Outcome("b", True, 300),
            Outcome("c", False, 50, "NoAudioReceived"),
        ]
    )
    assert "1 из 3" in text
    assert "NoAudioReceived" in text
    assert "200" in text  # median of the successful ones


def test_summary_needs_outcomes() -> None:
    with pytest.raises(ValueError):
        summarize([])
