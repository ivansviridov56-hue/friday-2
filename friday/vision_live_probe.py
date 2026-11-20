"""Live check of stage 10c: capture the screen and ask the vision chain about it.

Run: python -m friday.vision_live_probe ["question"]
The screenshot goes to the cloud provider. It is kept in memory only, nothing is saved.
"""

from __future__ import annotations

import logging
import sys
import time

from friday.llm import AllProvidersFailed
from friday.screen_capture import ScreenCaptureError, capture_screen
from friday.vision import DEFAULT_QUESTION, build_vision_client, describe

log = logging.getLogger(__name__)


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION

    try:
        shot = capture_screen()
    except ScreenCaptureError as exc:
        print(f"capture failed: {exc}")
        return
    print(f"screenshot {shot.width}x{shot.height}, {len(shot.data) // 1024} KB")

    started = time.perf_counter()
    try:
        reply = describe(build_vision_client(), shot, question)
    except AllProvidersFailed as exc:
        print(f"all providers failed: {exc}")
        return
    total = time.perf_counter() - started

    print(
        f"provider: {reply.provider}, model time {reply.latency_ms} ms, total {total:.1f} s"
    )
    print("answer:")
    print(reply.text)


if __name__ == "__main__":
    main()
