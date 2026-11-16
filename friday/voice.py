"""Voice assistant: hold mouse side button X2, speak, hear the answer.

The window runs on the main thread (PyWebView requires it); everything else
runs in a background thread. Closing the window stops the assistant.
"""

from __future__ import annotations

import logging
import threading

from friday.assistant import Assistant, Turn
from friday.audio import PygamePlayer
from friday.listening_indicator import ListeningIndicator
from friday.llm import LLMClient
from friday.mouse_trigger import XBUTTON2, SideButtonTrigger
from friday.persona import build_system_prompt
from friday.push_to_talk import PushToTalk
from friday.recorder import Recorder
from friday.stt import SpeechToText
from friday.tts import speak_text
from friday.turn_runner import TurnRunner
from friday.ui_events import UiEventBus
from friday.window import run_window

log = logging.getLogger(__name__)


def _show(turn: Turn | None) -> None:
    if turn is None:
        return
    print(f"Вы: {turn.heard}")
    if turn.reply is None:
        print("Пятница: [нейросеть недоступна]")
    else:
        print(
            f"Пятница [{turn.reply.provider}, {turn.reply.latency_ms} мс]: {turn.reply.text}"
        )


def _start_assistant(bus: UiEventBus, stop: threading.Event) -> None:
    """Background thread: load models, wire everything, wait until `stop`."""
    trigger = None
    recorder = None
    try:
        stt = SpeechToText()
        print("Прогреваю распознавание речи...")
        stt.warm_up_async().join()

        player = PygamePlayer()
        assistant = Assistant(
            stt,
            LLMClient(),
            lambda text: speak_text(text, player.play),
            system_prompt=build_system_prompt(),
            events=bus,
        )
        runner = TurnRunner(lambda audio: _show(assistant.handle_audio(audio)))
        indicator = ListeningIndicator(bus, lambda: runner.is_busy)

        def submit(audio) -> bool:
            accepted = runner.submit(audio)
            indicator.on_audio_submitted(accepted)
            return accepted

        def release() -> None:
            ptt.release()
            indicator.on_release()

        recorder = Recorder()
        recorder.open()
        ptt = PushToTalk(recorder, submit)

        def press() -> None:
            indicator.on_press()
            ptt.press()

        trigger = SideButtonTrigger(XBUTTON2, press, release)
        trigger.start()
        print(
            "Пятница готова. Зажми боковую кнопку мыши X2 и говори. Закрой окно: выход."
        )
        while not stop.wait(0.5):
            pass
    except Exception:
        log.exception("assistant crashed")
    finally:
        if trigger is not None:
            trigger.stop()
        if recorder is not None:
            recorder.close()


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)

    bus = UiEventBus()
    stop = threading.Event()
    worker = threading.Thread(
        target=_start_assistant, args=(bus, stop), name="assistant", daemon=True
    )
    worker.start()
    try:
        run_window(bus)  # blocks until the window is closed
    finally:
        stop.set()
        worker.join(timeout=5)


if __name__ == "__main__":
    main()
