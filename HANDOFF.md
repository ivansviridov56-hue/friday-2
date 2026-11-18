# Handoff (read this first in a new chat)

1. Read CLAUDE.md, then PROGRESS.md.
2. Ask the user to run `pytest` and paste the result (expect 315 passed).
3. Continue from the "Next" section of PROGRESS.md.
4. At the end of the session, update PROGRESS.md and this file.

## Current state
Stages 0-6 done: persona, LLM client with fallback chain, TTS (with retry), STT,
microphone capture, push-to-talk on mouse side button X2, dialogue memory,
conversation loop, desktop window (PyWebView, dark theme, chat + state indicator with a loading state).
Run it with `python -m friday.voice`. Repo is public on GitHub, CI should be green.
Next stage is not chosen yet.
Stage 7a-7c: track search and start by link done; 7d (voice command) next
Stages 0-7 done (Yandex Music: control, search, play a song by name)
Stages 0-7e done (Yandex Music: control, play a song by name, play an artist by name)

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
- Yandex Music is controlled through its own Windows media session (SMTC, winsdk),
  never through global media keys: those also hit browsers and other players.
  Local commands skip the LLM and are not stored in dialogue memory. Success confirmations of music commands are not spoken (window only); errors and “what’s playing” are spoken.
- Yandex Music by name: search needs `YM_TOKEN` in `.env` (variant A). The core (stage 6
  commands) works without a token. Without a token Friday says a token is needed.
  First phrases: "включи [track]" and "включи [artist] [track]"; whole artist later.
  A track is started through the link plus UI Automation invoke() on the track panel's
  button (found by structure, never by name or size alone), and success is confirmed via
  SMTC before Friday says "Включаю".
- Track choice: first search result that is available; versions like Instrumental / Karaoke /
  Acapella are skipped unless the phrase itself asks for them. If only such versions exist, the
  first available one is used.
- Voice feedback: commands with a search are spoken ("Включаю <artist>, <title>") once Music
  confirms playback, so a wrong match is heard at once. pause / play / next / previous stay silent.
- Play by name: only phrases with a play verb plus песня / трек / композиция (variant A, chosen by Claude on the user’s "делай как лучше"); "включи свет" and similar are not hijacked. Spoken confirmation "Включаю <artist>, <title>“ after SMTC confirms playback
- Stage 7e chosen by Claude on the user’s "выбери сам": play a whole artist by voice
- Stage 7e (play an artist) was chosen by Claude on the user’s "выбери сам"; marker word required (исполнитель / артист / группа)