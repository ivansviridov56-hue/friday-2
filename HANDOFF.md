# Handoff (read this first in a new chat)

1. Read CLAUDE.md, then PROGRESS.md.
2. Ask the user to run `pytest` and paste the result (expect 129 passed).
3. Continue from the "Next" section of PROGRESS.md.
4. At the end of the session, update PROGRESS.md and this file.

## Current state
Stages 0-5 done: persona, LLM client with fallback chain, TTS (with retry), STT,
microphone capture, push-to-talk on mouse side button X2, dialogue memory,
conversation loop, desktop window (PyWebView, dark theme, chat + state indicator).
Run it with `python -m friday.voice`. Repo is public on GitHub, CI should be green.
Next stage is not chosen yet.

## Decisions made
- Name: Friday 2.0, folder `Friday2`, public GitHub repo, MIT license.
- Interface: desktop window (PyWebView). Brain: cloud LLM, with a chain of
  free providers and fallback (no single provider, no VPN if possible).
- Ears: local faster-whisper large-v3-turbo on the GPU (RTX 5050, 8 GB).
  Cloudflare Whisper is a possible fallback, not needed so far.
- Activation: push-to-talk on mouse side button X2 (swallowed so the browser
  ignores it); wake word "Пятница" later.
- Free speech, not only short commands: the user wants to talk freely.
- Features to port from the old assistant: Yandex Music control, screen
  vision (describe a selected area), long-term memory.
- Not wanted: voice cloning (XTTS).
- Dependencies: requirements.txt is light (CI); requirements-local.txt has
  faster-whisper, sounddevice and CUDA packages for the user's machine.
- Dialogue memory: last 5 exchanges. First version: a new phrase is ignored while
  the assistant is answering (no interruption, no queue).
- Window v1: only the dialogue transcript and a state indicator (idle / listening /
  thinking / speaking), dark theme. No buttons, text input or settings yet.