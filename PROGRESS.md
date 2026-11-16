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

## Notes
- RTX 5050 (Blackwell) works with CTranslate2 4.9 once cuBLAS/cuDNN come from pip
  (nvidia-cublas-cu12, nvidia-cudnn-cu12); cuda_dlls.py registers their DLL dirs.
- First Whisper run is slow (JIT warm-up, up to ~30 s on an empty cache): always warm up.
- Whisper spells "Yandex Music" in Cyrillic and inflects it (Музик / Музыку / Мьюзик).
  Match commands by word stems ("яндекс", "музык"), not exact phrases.
- Rare Whisper slips on long phrases (one wrong word in 8 tries): fine for chat,
  keep in mind for commands.

## Next
Stage 3c: microphone capture + push-to-talk hotkey (record while the key is held,
return mono float32 16 kHz audio for SpeechToText). Wake word "Пятница" comes later.
Then: conversation loop (listen -> LLM -> speak).