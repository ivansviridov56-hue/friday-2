# Handoff (read this first in a new chat)

1. Read CLAUDE.md, then PROGRESS.md.
2. Ask the user to run `pytest` and paste the result (expect 924 passed).
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
Stage 10 (screen vision) done. 
Stage 11 (wake word) done: 11a-11e. The listener is wired into voice.py and OFF by default
(WAKE_WORD=1 in .env turns it on; WAKE_DEBUG=1 prints what was heard, for tuning only). Checked in
a quiet room and with music on speakers. 
Stage 12 (TTS fallback) done: Edge first (one try), the local Windows voice Irina for chunks Edge
cannot voice. Stage 13a done: music commands tolerate recognition slips (glued and smeared words).
Stage 13b done: My Wave works with a minimized Yandex Music window (a tray-hidden Music is not handled, see PROGRESS notes). The My Wave handler had been dropped from voice.py in stage 10d
and is wired in again.
Stage 13c done: after My Wave starts, a Yandex Music window that Friday restored is minimized back.
Stage 13d done: the handler chain is built by name in friday/command_chain.py (a missing handler fails at startup).
Stage 13e done: My Wave also works with Yandex Music closed (the wave link is opened only when no Music process exists).
Stage 13f done: the main voice is local Silero v5_ru (kseniya); Edge is an option via TTS_ENGINE=edge.
Stage 13g done: Latin words are spelled in Cyrillic before the Silero voice (friday/translit.py).
Stage 15a done: new window design (friday/ui/: index.html, styles.css, app.js), circle colour follows the state.
Stage 15b done: circles follow the microphone loudness while listening (level_meter.py, level_publisher.py).
Stage 16 done: text input in the window (friday/text_input.py, field under the chat); typed text goes the same way as a phrase from the wake listener.
Stage 17 done: frameless window with own minimize / close buttons, drag by the header, resize by the right / bottom edge and corner (friday/window_controls.py, friday/window_api.py).
Stage 18 done: window layout (chat column on the left, island input bar, music circle placeholder); the look of the circles is open.
Stage 18b done: input island (compact, opens on hover / focus / text, grows with the text, Enter sends, Shift+Enter adds a line). Slight text jitter on fast typing is a known postponed issue.
Stage 18c done: input island smaller, slower opening, raised. Stage 19a done: the music circle shows the cover of the current Yandex Music track (hidden when Music is closed, stays on pause); friday/cover_publisher.py + cover_source.py; animations of the circle postponed.
Stage 20a done: the look of the background circles is switchable by CIRCLES in .env (classic, blobs, equalizer, dots); each look is one file in friday/ui/circles/; the choice in the app settings comes later.
Next: see the Next section of PROGRESS.md.

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
- Wake word "Пятница": energy segmenter cuts the microphone stream into phrases, local Whisper
  recognizes each, the phrase must START with the name (fuzzy match). Name + command in one phrase
  is sent at once; the name alone waits up to 6 s for the next phrase. The listener is deaf while the
  assistant answers or X2 is held, and 1 s after. Phrase texts are not logged unless WAKE_DEBUG=1.
  X2 push-to-talk stays. Not hijacking: phrases without the name are dropped.
- TTS: Edge TTS (Svetlana) first, one try; if it fails, that chunk goes to the local Windows voice
  "Microsoft Irina Desktop" (PowerShell System.Speech, text in a base64 env variable). Edge failures
  are on the service side (not parallelism, rate, punctuation or library version).
- My Wave with closed Music (13e): the wave link is opened only when no Music process exists (it does
  not switch the page of a running app). A failed cold start keeps the generic NO_PLAYER answer; a
  separate "Music did not start" status is postponed until it happens live (chosen by Claude on the
  user's "решай сам").
- TTS engine (13f): Silero v5_ru (local, CPU, voice kseniya, chosen by the user after listening)
  is the main voice; Edge stays as an option via TTS_ENGINE=edge (with the Windows fallback voice
  as before). No Edge-first/Silero-fallback chain (chosen by Claude on the user's "решай сам").
  Probe: model loads in ~9 s, synthesis 55-106 ms per ~5 s of audio. The model is never committed
  to the repo; the licence note goes to README.
- 13f, last open point: the startup window (a phrase before Silero has loaded) was checked by a test, not
  live; the voice waits for the model, nothing is lost (chosen by Claude on the user's "выбери сам").
- 13g: Silero does not read Latin letters, so text is converted to Cyrillic right before synthesis
  (small dictionary + letter-by-letter fallback); one voice, no English model (variant A, chosen by
  the user: "сделаем так, а дальше посмотрим"). Screen-description answers are left long on purpose:
  the user is fine with the speed, shorten only if it starts to bother.
- Window design (15a): taken from the user's old project (look only, no old code); the page API
  window.fridayUi.setState / addMessage must stay the same. Sidebar sections and the text input are
  postponed until there are features behind them (chosen by the user).
- Circles and sound (15b): only the user's voice for now (variant A, chosen by the user); loudness goes
  to the window only in the LISTENING state; her own voice moving the circles is a later step (variant B).
- Text input (16): typed text is handed to TurnRunner.submit like a phrase after the wake word, so all
  voice commands work from the keyboard. While she is busy or still loading the text is refused and
  stays in the field (the field flashes red). Maximum 500 characters; the text is never logged. The look
  of the field is temporary until the window design is decided (the user explored a black glass design
  in Figma and went back; nothing from it is in the code).
- Window frame (17): no system frame; only minimize and close (the user does not want maximize).
  Resizing works only from the right edge, the bottom edge and the corner (variant A, chosen by the user);
  left and top edges are not supported. The page can call only the methods listed in WindowApi.
- Window layout (18): the chat column is on the left, the input is a floating glass "island" under it with a
  round music circle beside it; no title in the island, no dots, no hint, no microphone button (the user's
  decisions). The circles are not blurred for now (blur caused banding); their final look is still to be
  decided (the user: "maybe replace them with something else"). A black Windows-like theme is a possible
  later step.
- Input island (18b): no state hint in the placeholder and no state glow, only the nudge on refusal (the user's decision). Compact by default and opens on hover or focus; stays open while there is text. The island animates its height, the text area does not. Shift+Enter jitter on fast typing is postponed by the user.
- Input island (18c): closed 220 px, open 400 px, slow opening, raised; the user is happy (take 7 in styles.css).
- Music circle (19a): cover first, control later as 19b (chosen by the user). On pause the circle stays; it is hidden only when there is no cover or Music is closed. Animations are postponed by the user.
- Circles looks (20a): four looks, chosen through .env for now (variant A, chosen by the user), a choice inside the app settings later. The user liked the blobs, the equalizer and the dots from the preview page and wants to tune each one separately. The window jitter at start is postponed by the user (smooth appearance later).