"""Voice assistant: hold mouse side button X2, speak, hear the answer.

The window runs on the main thread (PyWebView requires it); everything else
runs in a background thread. Closing the window stops the assistant.
"""

from __future__ import annotations

import logging
import os
import threading

from pathlib import Path

from friday.screen_capture import capture_screen
from friday.screen_handler import make_screen_handler
from friday.vision import build_vision_client, describe
from friday.wave_handler import make_wave_handler
from friday.wave_ui import build_launcher as build_wave_launcher
from friday.history import ConversationHistory
from friday.memory_prompt import with_facts
from friday.memory_handler import make_memory_handler
from friday.memory_store import MemoryStore
from friday.assistant import Assistant, Turn
from friday.audio import PygamePlayer
from friday.listening_indicator import ListeningIndicator
from friday.llm import LLMClient
from friday.mouse_trigger import XBUTTON2, SideButtonTrigger
from friday.music import MusicController
from friday.music_handler import make_music_handler
from friday.smtc import list_sessions
from friday.persona import build_system_prompt
from friday.push_to_talk import PushToTalk
from friday.recorder import Recorder
from friday.stt import SpeechToText
from friday.tts import speak_text
from friday.turn_runner import TurnRunner
from friday.ui_events import State, StateChanged, UiEventBus
from friday.window import run_window
from friday.music_search import TrackSearch
from friday.play_handler import chain_handlers, make_play_handler
from friday.ym_ui import build_launcher
from friday.artist_handler import make_artist_handler
from friday.artist_search import ArtistSearch
from friday.ym_artist_ui import build_artist_launcher

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = PROJECT_ROOT / "data" / "memory" / "facts.json"


def _show(turn: Turn | None) -> None:
    if turn is None:
        return
    print(f"Вы: {turn.heard}")
    if turn.local_reply is not None:
        print(f"Пятница [команда]: {turn.local_reply}")
    elif turn.reply is None:
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
        bus.publish(StateChanged(State.LOADING))
        stt = SpeechToText()
        print("Прогреваю распознавание речи...")
        stt.warm_up_async().join()

        player = PygamePlayer()

        def speak(text: str) -> None:
            speak_text(text, player.play)

        vision_client = build_vision_client()
        token = os.environ.get("YM_TOKEN")
        memory = MemoryStore(MEMORY_FILE)
        history = ConversationHistory()
        assistant = Assistant(
            stt,
            LLMClient(),
            speak,
            system_prompt=lambda: with_facts(build_system_prompt(), memory.facts()),
            events=bus,
            history=history,
            commands=chain_handlers(
                make_memory_handler(memory, on_forgotten=history.clear),
                make_screen_handler(
                    capture_screen,
                    lambda shot, question: describe(vision_client, shot, question),
                    announce=speak,
                ),
                make_play_handler(TrackSearch(token), build_launcher()),
                make_artist_handler(ArtistSearch(token), build_artist_launcher()),
                make_music_handler(MusicController(list_sessions)),
            ),
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
        bus.publish(StateChanged(State.IDLE))
        print(
            "Пятница готова. Зажми боковую кнопку мыши X2 и говори. Закрой окно: выход."
        )
        while not stop.wait(0.5):
            pass
    except Exception:
        log.exception("assistant crashed")
        bus.publish(StateChanged(State.ERROR))
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
