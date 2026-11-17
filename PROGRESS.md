# Progress

## Done

- [x] Stage 0: foundation
  - Python 3.11.9, git, VS Code, .venv, pytest
  - Skeleton + smoke tests (2 passed)
  - CLAUDE.md, HANDOFF.md, PROGRESS.md, README (en/ru), LICENSE (MIT)
  - Public repo: https://github.com/ivansviridov56-hue/friday-2
  - GitHub Actions runs pytest on every push (green)

- [x] Stage 1a: probe tools (probe.py, scan.py, catalog.py, cf_probe.py), 19 tests
  - [x] Free LLM sources reachable from Belarus without VPN: Cloudflare Workers AI
    (460-800 ms), OpenRouter free models (limited daily quota)
  - [x] Not available: Groq, Cerebras, NVIDIA (phone check), Mistral (paid), Gemini (no VPN)

- [x] Stage 1b: Russian quality bench; chain: Cloudflare mistral-small-3.1 -> llama-3.3-70b -> OpenRouter free

- [x] Stage 2: persona (feminine, informal) + LLM client with fallback chain, 37 tests

- [x] Stage 3a: TTS (Edge, voice Svetlana +30%), chunked + prefetched playback,
      first sound in ~1.2-1.9 s, 55 tests

- [x] Stage 3b: STT (faster-whisper large-v3-turbo, float16 on RTX 5050), 63 tests
  - friday/stt.py (SpeechToText, lazy load, background warm-up), friday/cuda_dlls.py
  - Checked by voice: ~0.5 s per 5 s of audio, warm-up ~4 s, silence returns ""
  - CI installs only requirements.txt (light); heavy deps live in requirements-local.txt
- [x] Stage 3c: push-to-talk on mouse side button X2, 91 tests
  - friday/recorder.py (mic stream stays open, audio kept only while recording)
  - friday/push_to_talk.py (press/release logic, presses under 0.3 s discarded)
  - friday/mouse_trigger.py (global hook via pynput, swallows X2 so the browser
    does not go "forward"; callbacks run in a worker thread, not in the hook)
  - Checked by voice: first word is not cut off, short clicks are discarded

- [x] Stage 4: conversation loop, console version, 112 tests
  - friday/history.py (last 5 exchanges, an exchange is stored only after a successful reply)
  - friday/assistant.py (one turn: audio -> STT -> LLM -> TTS; spoken failure phrase
    if all providers fail; a broken speaker does not kill the loop)
  - friday/turn_runner.py (one turn at a time in a background thread, so the mouse
    hook thread never blocks; new audio during an answer is dropped and logged)
  - friday/voice.py: `python -m friday.voice`, glue only, checked live (no unit tests)
  - TTS: retry with a short pause when Edge returns no audio (3 attempts)
  - Checked by voice: dialogue memory works, phrase during an answer is ignored,
    the assistant answers again afterwards, Ctrl+C exits

- [x] Stage 5: PyWebView window, 129 tests
  - friday/ui_events.py (thread-safe event bus: StateChanged, MessageAdded)
  - friday/assistant.py publishes events (THINKING, messages, SPEAKING, IDLE)
  - friday/ui_bridge.py (events -> JS calls, queued until the page has loaded)
  - friday/listening_indicator.py (LISTENING only when free; back to IDLE on a short or dropped press)
  - friday/ui/index.html (dark theme, chat bubbles, state dot), friday/window.py (live-checked, no unit tests)
  - friday/voice.py: window on the main thread, assistant in a background thread,
    closing the window stops everything
  - Checked by voice: states change in the right order, short click blinks and returns
    to idle, phrase during an answer is ignored, closing the window exits cleanly

- [x] Stage 5b: "loading" state in the window, 132 tests
  - State.LOADING; the window shows a pulsing dot and "Загружаюсь…" until the
    assistant is ready (microphone and mouse trigger started)
  - UiEventBus remembers the last state and gives it to a late subscriber
    (the assistant thread can publish before the window subscribes)
  - Checked live: loading -> idle after Whisper warm-up, then normal dialogue

- [x] Stage 6: Yandex Music control, 197 tests
  - friday/smtc.py (the only module that imports winsdk; live-checked), friday/music.py
    (MusicController: a command goes only to the Yandex Music media session, never to
    a browser or another player), friday/ym_probe.py (diagnostic: lists media sessions)
  - friday/music_commands.py (word-stem parser; needs a music word and a short phrase,
    so free conversation is not hijacked), friday/music_handler.py (glue)
  - Assistant takes an optional `commands` handler: a command is answered locally,
    skips the LLM and is not stored in dialogue memory
  - Checked by voice: pause / play / next / previous / what's playing; Music closed ->
    Friday says she cannot see it; ordinary speech still goes to the LLM

  - [x] Stage 6b: "error" state in the window, 199 tests
  - State.ERROR; if the assistant crashes while loading, the window turns red with
    "Ошибка запуска. Подробности в консоли." (details stay in the console log)

## Notes
- RTX 5050 (Blackwell) works with CTranslate2 4.9 once cuBLAS/cuDNN come from pip
  (nvidia-cublas-cu12, nvidia-cudnn-cu12); cuda_dlls.py registers their DLL dirs.
- First Whisper run is slow (JIT warm-up, up to ~30 s on an empty cache): always warm up.
- Whisper spells "Yandex Music" in Cyrillic and inflects it (Музик / Музыку / Мьюзик).
  Match commands by word stems ("яндекс", "музык"), not exact phrases.
- Rare Whisper slips on long phrases (one wrong word in 8 tries): fine for chat,
  keep in mind for commands.
- The always-open microphone keeps the Windows "mic in use" indicator on while
  the assistant runs. Needed later for the wake word "Пятница" anyway.
- Windows ignores a global hook for windows that run as administrator, unless
  the assistant also runs as administrator.
- Edge TTS sometimes returns NoAudioReceived; retry fixed it in live runs. Synthesis
  speed varies from 1.3 s to 4 s per chunk (service side). If it bothers us, try
  MAX_PARALLEL = 1.
- On Windows `threading.Event().wait()` blocks Ctrl+C; wait in a loop with a timeout.
- chat.py still has its own history (trim_history); it is a manual tool, not migrated
  to ConversationHistory.
- Known quality issues: the free LLM sometimes invents facts and slips into masculine
  forms; Whisper hears "Пятница" as "Бэтни" and similar.
- PyWebView must run on the main thread. pywebview is in requirements-local.txt only (CI stays light).
- "Previous" in Yandex Music first rewinds the current track to the start; repeat the
  command to go to the previous one (app behaviour, left as is by the user's decision).
- Music command stems in music_commands.py are tuned for Whisper output. If a phrase
  misfires or is missed, the log has "music command X from '...'" and the "Вы:" line.
- Successful play / pause / next / previous answers are shown in the window but not
  spoken (so quick repeated commands are not lost while she talks). Errors and
  "what's playing" are spoken.
- Not done: playing a specific track and "My Wave". Needs a decision (yandex-music
  token vs window automation). The old project has both: D:\Project\Friday\music\yandex.py.

## Next
Not chosen yet (ask the user). Candidates: wake word "Пятница", Yandex Music: play a specific track / My Wave (decision needed),
screen vision, long-term memory. Skipped for now
(user's decision): quality polish of persona and STT hints.