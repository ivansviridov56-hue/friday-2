"""Probe for stage 12: how often does Edge TTS return no audio?

Run: python -m friday.tts_probe
Compares one request at a time with two at a time (what speak_async does now), using
the phrases that failed in the live log plus plain ones. No retries, nothing is played
or saved. Takes about a minute.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import sys
import time
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from friday.tts import TtsSettings, synthesize

log = logging.getLogger(__name__)

PHRASES = [
    "Сейчас играет BUSHIDO ZHO, Джо",
    "ENTYPE, Мои клиенты.",
    "Мои клиенты.",
    "На паузе: BUSHIDO ZHO, Джон Гарик, FEDUK, ENTYPE, Мои клиенты.",
    "Поставила на паузу.",
    "У меня всё отлично, босс.",
    "Я рада быть на связи.",
    "Чем могу быть полезна?",
    "Включаю следующий.",
    "Сейчас играет Каста, Ды-ды-дым.",
]
ROUNDS = 2

RATE_TEXTS = [
    "Мои клиенты.",
    "Мои клиенты",
    "Сейчас играет BUSHIDO ZHO, Джо",
    "Сейчас играет Каста, Ды-ды-дым.",
    "Поставила на паузу.",  # control: never failed
]
RATES = ["+0%", "+30%"]
RATE_ROUNDS = 3

Synth = Callable[[str], Awaitable[bytes]]


@dataclass(frozen=True)
class Outcome:
    text: str
    ok: bool
    ms: int
    error: str = ""


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


async def _one(text: str, synth: Synth) -> Outcome:
    started = time.perf_counter()
    try:
        await synth(text)
    except Exception as exc:  # the probe counts failures, it must not stop on them
        return Outcome(text, False, _elapsed_ms(started), type(exc).__name__)
    return Outcome(text, True, _elapsed_ms(started))


async def run_round(phrases: list[str], synth: Synth, parallel: int) -> list[Outcome]:
    """Synthesize every phrase, at most `parallel` at the same time."""
    gate = asyncio.Semaphore(parallel)

    async def limited(text: str) -> Outcome:
        async with gate:
            return await _one(text, synth)

    return list(await asyncio.gather(*(limited(text) for text in phrases)))


def summarize(outcomes: list[Outcome]) -> str:
    if not outcomes:
        raise ValueError("no outcomes to summarize")
    failed = [o for o in outcomes if not o.ok]
    times = [o.ms for o in outcomes if o.ok]
    median = int(statistics.median(times)) if times else 0
    errors = sorted({o.error for o in failed}) or ["нет"]
    return (
        f"не получили звук {len(failed)} из {len(outcomes)}, "
        f"медиана {median} мс, самый долгий {max(times, default=0)} мс, "
        f"ошибки: {', '.join(errors)}"
    )


async def main_async() -> None:
    settings = TtsSettings()

    async def synth(text: str) -> bytes:
        return await synthesize(text, settings)

    results: dict[int, list[Outcome]] = {1: [], 2: []}
    for _ in range(ROUNDS):  # alternate, so the time of day does not favour one mode
        for parallel in (1, 2):
            results[parallel] += await run_round(PHRASES, synth, parallel)
            print(f"... по {parallel} за раз: раунд готов")
    print()
    for parallel, outcomes in results.items():
        print(f"по {parallel} за раз: {summarize(outcomes)}")
    failed = Counter(o.text for out in results.values() for o in out if not o.ok)
    if failed:
        print("\nЧто падало (раз, фраза):")
        for text, count in failed.most_common():
            print(f"  {count}x {text!r}")


async def main_rates_async() -> None:
    """The texts that always fail: does the speaking rate or the final period matter?"""
    table: dict[tuple[str, str], list[Outcome]] = {}
    for _ in range(RATE_ROUNDS):
        for rate in RATES:
            settings = TtsSettings(rate=rate)

            async def synth(text: str, settings: TtsSettings = settings) -> bytes:
                return await synthesize(text, settings)

            for outcome in await run_round(RATE_TEXTS, synth, parallel=1):
                table.setdefault((outcome.text, rate), []).append(outcome)
    print(f"\nне получили звук (из {RATE_ROUNDS}):")
    print(f"{'':38}" + "".join(f"{rate:>8}" for rate in RATES))
    for text in RATE_TEXTS:
        cells = "".join(f"{sum(not o.ok for o in table[(text, r)]):>8}" for r in RATES)
        print(f"{text[:36]!r:38}{cells}")


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    if "rates" in sys.argv[1:]:
        asyncio.run(main_rates_async())
    else:
        asyncio.run(main_async())


if __name__ == "__main__":
    main()
