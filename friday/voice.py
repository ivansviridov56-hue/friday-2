"""Voice assistant: hold mouse side button X2, speak, hear the answer."""

from __future__ import annotations

import threading
import logging

from friday.assistant import Assistant, Turn
from friday.audio import PygamePlayer
from friday.llm import LLMClient
from friday.mouse_trigger import XBUTTON2, SideButtonTrigger
from friday.persona import build_system_prompt
from friday.push_to_talk import PushToTalk
from friday.recorder import Recorder
from friday.stt import SpeechToText
from friday.tts import speak_text
from friday.turn_runner import TurnRunner

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


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)

    stt = SpeechToText()
    print("Прогреваю распознавание речи...")
    stt.warm_up_async().join()

    player = PygamePlayer()
    assistant = Assistant(
        stt,
        LLMClient(),
        lambda text: speak_text(text, player.play),
        system_prompt=build_system_prompt(),
    )
    runner = TurnRunner(lambda audio: _show(assistant.handle_audio(audio)))

    recorder = Recorder()
    recorder.open()
    ptt = PushToTalk(recorder, runner.submit)
    trigger = SideButtonTrigger(XBUTTON2, ptt.press, ptt.release)
    trigger.start()
    print("Пятница готова. Зажми боковую кнопку мыши X2 и говори. Ctrl+C: выход.")
    try:
        stop = threading.Event()
        while not stop.wait(0.5):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        trigger.stop()
        recorder.close()


if __name__ == "__main__":
    main()
