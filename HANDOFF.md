# Handoff (read this first in a new chat)

1. Read CLAUDE.md, then PROGRESS.md.
2. Ask the user to run `pytest` and paste the result (expect 541 passed).
3. Continue from the "Next" section of PROGRESS.md.
4. At the end of the session, update PROGRESS.md and this file.

## Current state
Stages 0-8e done: persona, LLM client with fallback chain, TTS (with retry), STT,
microphone capture, push-to-talk on mouse side button X2, dialogue memory,
conversation loop, desktop window (PyWebView, dark theme, chat + state indicator
with loading and error states), Yandex Music (control, play a song by name,
play an artist by name).
Stage 9: My Wave by voice.
Run it with `python -m friday.voice`. Repo is public on GitHub, CI should be green.
Stage 10 (screen vision): 10a-10d done (probes, capture, vision client, voice command "что на экране"). Left: privacy note about screenshots in both readmes.

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
  thinking / speaking, plus loading and error), dark theme. No buttons, text input
  or settings yet.
- Yandex Music is controlled through its own Windows media session (SMTC, winsdk),
  never through global media keys: those also hit browsers and other players.
  Local commands skip the LLM and are not stored in dialogue memory. Success
  confirmations of pause / play / next / previous are not spoken (window only);
  errors and "what's playing" are spoken.
- Yandex Music by name: search needs `YM_TOKEN` in `.env` (variant A). The core (stage 6
  commands) works without a token. Without a token Friday says a token is needed.
  A track is started through the link plus UI Automation invoke() on the track panel's
  button (found by structure, never by name or size alone), and success is confirmed via
  SMTC before Friday says "Включаю".
- Track choice: first search result that is available; versions like Instrumental / Karaoke /
  Acapella are skipped unless the phrase itself asks for them. If only such versions exist, the
  first available one is used.
- Voice feedback: commands with a search are spoken ("Включаю <artist>, <title>") once Music
  confirms playback, so a wrong match is heard at once.
- Play by name: only phrases with a play verb plus песня / трек / композиция (variant A,
  chosen by Claude on the user's "делай как лучше"); "включи свет" and similar are not hijacked.
- Play an artist: stage 7e, chosen by Claude on the user's "выбери сам"; a marker word is
  required (исполнитель / артист / певец / группа), bare "включи Киркорова" is not a command.
- Stage 8 (long-term memory) chosen by Claude on the user's "выбери сам": testable without
  extra providers, unlike the wake word (Whisper mishears the name) and screen vision.
- Long-term memory: facts only on an explicit phrase ("запомни ..."), stored in
  data/memory/facts.json (git-ignored), memory commands are local (no LLM, not stored in
  dialogue memory), all facts go to the system prompt (8d).
  ”забудь" that really removed facts also clears the dialogue history (8e, chosen by Claude on the user’s "как хочешь")
- My Wave: "включи мою волну" starts the wave through the wave player block (found by structure,
  pressed only if the middle button is named "Воспроизведение", confirmed via SMTC). If the wave
  page is not open, Friday says so; opening it via the menu is a later stage (variant A, chosen
  by Claude on the user's "выбери сам"). Only the plain command; "by mood" and similar are not
  hijacked. NOT_CONFIRMED has its own spoken answer, ERROR a generic one (chosen by Claude on
  the user's "делай как лучше").
- Screen description by voice