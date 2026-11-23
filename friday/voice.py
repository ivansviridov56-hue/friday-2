"""Voice assistant: hold mouse side button X2, speak, hear the answer.

The window runs on the main thread (PyWebView requires it); everything else
runs in a background thread. Closing the window stops the assistant.
"""

from __future__ import annotations

import logging
import os
import threading

from pathlib import Path

from friday.wallpaper_source import FileWallpaperSource
from friday.wallpaper_watcher import WallpaperWatcher
from friday.accent_publisher import AccentPublisher
from friday.accent_source import RegistryAccentSource
from friday.settings_service import SettingsService
from friday.settings_store import SettingsStore
from friday.text_input import TextInput
from friday.window_api import WindowApi
from friday.window_controls import WindowControls
from friday.wake_listener import WakeListener
from friday.wake_setup import SerializedTranscriber, WakeIndicator, env_flag
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
from friday.cover_publisher import CoverPublisher
from friday.cover_source import SmtcCoverSource
from friday.level_publisher import LevelPublisher
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
from friday.tts_choice import choose_tts
from friday.turn_runner import TurnRunner
from friday.ui_events import State, StateChanged, UiEventBus, WallpaperChanging
from friday.window import run_window
from friday.music_search import TrackSearch
from friday.command_chain import build_command_chain
from friday.play_handler import make_play_handler
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


def _start_assistant(
    bus: UiEventBus, stop: threading.Event, text_input: TextInput
) -> None:
    """Background thread: load models, wire everything, wait until `stop`."""
    trigger = None
    listener = None
    recorder = None
    level_publisher = None
    cover_publisher = None
    try:
        bus.publish(StateChanged(State.LOADING))
        tts_choice = choose_tts(os.environ.get("TTS_ENGINE"))

        def _warm_up_voice() -> None:
            try:
                tts_choice.warm_up()
            except Exception:
                log.exception("voice warm-up failed")

        threading.Thread(target=_warm_up_voice, name="tts-warm-up", daemon=True).start()
        stt = SpeechToText()
        print("Прогреваю распознавание речи...")
        stt.warm_up_async().join()
        shared_stt = SerializedTranscriber(stt)

        player = PygamePlayer()

        def speak(text: str) -> None:
            speak_text(text, player.play, engine=tts_choice.engine)

        vision_client = build_vision_client()
        token = os.environ.get("YM_TOKEN")
        memory = MemoryStore(MEMORY_FILE)
        history = ConversationHistory()
        assistant = Assistant(
            shared_stt,
            LLMClient(),
            speak,
            system_prompt=lambda: with_facts(build_system_prompt(), memory.facts()),
            events=bus,
            history=history,
            commands=build_command_chain(
                {
                    "memory": make_memory_handler(memory, on_forgotten=history.clear),
                    "screen": make_screen_handler(
                        capture_screen,
                        lambda shot, question: describe(vision_client, shot, question),
                        announce=speak,
                    ),
                    "wave": make_wave_handler(build_wave_launcher()),
                    "play": make_play_handler(TrackSearch(token), build_launcher()),
                    "artist": make_artist_handler(
                        ArtistSearch(token), build_artist_launcher()
                    ),
                    "music": make_music_handler(MusicController(list_sessions)),
                }
            ),
        )

        def run_turn(item) -> None:
            if isinstance(
                item, str
            ):  # a phrase already recognized by the wake listener
                _show(assistant.handle_text(item))
            else:
                _show(assistant.handle_audio(item))

        runner = TurnRunner(run_turn)
        text_input.set_handler(runner.submit)
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
        level_publisher = LevelPublisher(bus, recorder)
        level_publisher.start()
        cover_publisher = CoverPublisher(bus, SmtcCoverSource())
        cover_publisher.start()
        ptt = PushToTalk(recorder, submit)
        if env_flag(os.environ.get("WAKE_WORD")):
            wake_indicator = WakeIndicator(bus)
            listener = WakeListener(
                recorder,
                shared_stt,
                runner.submit,
                lambda: runner.is_busy or recorder.is_recording,
                on_event=wake_indicator.on_event,
                log_text=env_flag(os.environ.get("WAKE_DEBUG")),
            )
            listener.start()
            print('Слово-активатор включено: скажи "Пятница, ..."')

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
        text_input.set_handler(None)
        if listener is not None:
            listener.stop()
        if trigger is not None:
            trigger.stop()
        if level_publisher is not None:
            level_publisher.close()
        if cover_publisher is not None:
            cover_publisher.close()
        if recorder is not None:
            recorder.close()


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)

    bus = UiEventBus()
    settings = SettingsService(bus, SettingsStore(), os.environ)
    settings.publish_initial()
    accent_publisher = AccentPublisher(bus, RegistryAccentSource())
    accent_publisher.start()
    wallpaper_watcher = WallpaperWatcher(
        FileWallpaperSource(), lambda: bus.publish(WallpaperChanging())
    )
    wallpaper_watcher.start()
    stop = threading.Event()
    text_input = TextInput()
    controls = WindowControls()
    worker = threading.Thread(
        target=_start_assistant,
        args=(bus, stop, text_input),
        name="assistant",
        daemon=True,
    )
    worker.start()
    try:
        run_window(
            bus, WindowApi(text_input, controls, settings), controls
        )  # blocks until closed
    finally:
        stop.set()
        accent_publisher.close()
        wallpaper_watcher.close()
        worker.join(timeout=5)


if __name__ == "__main__":
    main()
