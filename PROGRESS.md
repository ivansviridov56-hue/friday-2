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

## Next
Stage 5: PyWebView window. Later: wake word "Пятница", Yandex Music, screen vision,
long-term memory. Skipped for now (user's decision): quality polish of persona and
STT hints (feminine forms, "not sure" instead of invented facts, "Пятница" prompt).