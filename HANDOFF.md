# Handoff (read this first in a new chat)

1. Read CLAUDE.md, then PROGRESS.md.
2. Ask the user to run `pytest` and paste the result (expect 1626 passed).
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
Stage 21 done: colour themes (THEME in .env: classic, windows, black; one CSS file per theme in friday/ui/themes/) and state colours for the 
grey themes; the choice in the app settings comes later.
Stage 22a done: settings screen (gear in the header, panel on the right) with the theme and the look of the circles; the choice is saved in data/settings.json and wins over .env.
Stage 23 done: theme "win11" with a real blurred window background (friday/backdrop_logic.py, friday/win_backdrop.py, friday/ui/themes/win11.css); the blur stays when the window is inactive. Accent is fixed for now.
Stage 23d done: the accent colour of the win11 theme follows the Windows accent (friday/accent_*.py), re-read every 3 s.
Stage 23e done: a dark veil hides the abrupt blur redraw when the wallpaper changes (friday/wallpaper_source.py, friday/wallpaper_watcher.py, event WallpaperChanging); now works in every theme (stage 24f).
Stage 24 done: window transparency slider in the settings, saved per theme (friday/transparency.py, friday/backdrop_tint.py, class Backdrop in friday/win_backdrop.py); in win11 it moves the Windows tint, in the other themes it thins the page background over a fixed tint.
Stage 24e done: each theme has its own colour under the transparent page (TINT_COLORS and tint_for in friday/backdrop_logic.py: classic #0c0f1d, windows #202020, black #010101, win11 #202020); the page no longer paints its own background; at 100 % only the blur is left. Black uses #010101, because a fully black tint with opacity 0 makes Windows draw its own black (guarded by a test).
Stage 24f done: the wallpaper veil works in every theme, not only in win11 (the win11-only check was removed from coverWallpaperChange in friday/ui/app.js; the veil rules moved from themes/win11.css to styles.css; the veil colour follows the theme: classic #0c0f1d, black #010101, others #202020).
Stage 25a done: tray icon (friday/tray.py, pystray + pillow) with the menu "Открыть" / "Выйти"; the window's X button and Alt+F4 only hide the window, the app exits only through the tray "Выйти" (friday/window_lifecycle.py, wired in friday/window.py and friday/voice.py). Voice, wake word and X2 keep working with the window hidden. The minimize button still minimizes to the taskbar.
Stage 25b done: the top-edge island is a Qt (PySide6) window in its own process (friday/island_qt.py window, island_process.py control, island_bridge.py forwarding of state, theme and answer text, island_logic.py colours and clip_text); hangs from the top edge like a notch, colours follow the window theme, shows her answer (up to two lines) and hides it 1.5 s after she stops speaking; always visible for now. Next: replace the dot, island settings.
Stage 25b-7 done (wavy edge of the island, transparency fixed). Stage 26 done: the island reveals the
answer text in step with her voice (text_reveal.py, SpeechChunkStarted, reveal / chunk / done channels).
Stage 27 done (smoother island, fps counter FRIDAY_ISLAND_FPS=1). Stage 28 done: the island is a Qt Quick
window (friday/island_quick.py, friday/ui/island.qml, island_model.py, island_shape.py), the old island_qt.py
is removed; the jitter is gone (the layered-window hypothesis was right). The protocol (stdin) and
island_process.py / island_bridge.py are unchanged. Postponed by the user. Stage 27e done: words fade in on the island (friday/word_fade.py, IslandModel.markup, StyledText in island.qml).
Stage 29 done: the island icon has three looks (dot, eyes, equalizer), chosen in the settings (friday/island_looks.py, island_look in data/settings.json).
Stage 30 done: the island icon has a fourth look "blobs" (soft spots, drawn with a radial gradient: SOFT_LOOKS / is_soft_look in friday/island_looks.py, iconSoft in friday/island_quick.py).
Stage 14 done: My Wave by mood ("включи мою спокойную волну": active / fun / calm / sad). Files:
friday/wave_mood.py (logic), wave_mood_ui.py (UI Automation), wave_mood_handler.py (spoken answers);
the handler "wave_mood" stands before "wave" in friday/command_chain.py. Checked by voice.
Stage 31 done: in the win11 theme the island icon (idle and loading) follows the Windows accent (color_for with accent in friday/island_logic.py, command "accent" on the island stdin channel).
Stage 32 done: start a My Wave card by its title ("включи волну <name>"): friday/wave_cards.py,
wave_card_launcher.py, wave_card_ui.py, wave_card_handler.py; handler "wave_card" stands between
"wave_mood" and "wave". Checked by voice. 32d (search fallback) is postponed. Details and open
points are in PROGRESS.md.
Stage 33 done (checked live): the window is cloaked until it is ready and fades in; it fades out on X
and fades in from the tray (window_reveal.py, win_cloak.py, window_fade.py, win_fade.py).
Next: Windows-like minimize (see PROGRESS.md, stage 33).

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
- Themes (21): three themes, chosen through .env for now, in-app settings later (the user's wish, like the circles). Only colours change, not shapes or fonts (the user's decision). The grey theme has no blue anywhere. State colours are per theme: calm for windows, brighter for black; the user left them as they are for now.
- Settings screen (22a): opens from a gear in the header, a panel slides in on the right (variant A, chosen by the user). A choice applies at once, no save button, and is saved in data/settings.json (git-ignored); a saved choice wins over THEME / CIRCLES in .env, which stay as the starting values. The page only asks; Python checks the value and writes the file. First version holds only the theme and the circles look.
- Windows 11 theme (23): shapes as in the other themes; colours and accent follow the wallpaper like in Windows (the user's wish); blur and transparency are real, not drawn in CSS. Mica / Acrylic were rejected because they go flat when the window is inactive; the old acrylic with a "kick" is used instead. Tint 60 %, set by the user (variant C): a slider in the settings later.
- Accent (23d): index 1 of AccentPalette is the accent, index 0 the light shade. It paints only the user's bubble, the idle circles and the chosen option in the settings; everything else stays neutral (variant chosen by Claude, the user accepted it after seeing it). It applies only in the win11 theme. Colours fade smoothly (1.2 s); polling 0.5 s.
- Wallpaper change (23e): the blur snap of Windows cannot be removed, so it is hidden under a veil that fades in on the wallpaper file change and out after the new accent arrives (the user's idea, chosen by the user over redrawing the blur in CSS). Opacity 0.99 (checked live). A short dark pause on every wallpaper change is accepted by the user.
- Transparency (24e): one slider, 0-100 %, each theme keeps its own value (user's wish); defaults 0 % except win11 40 % (= the old 60 % tint). The slider changes only the density of the theme's own tint colour under the transparent page, so at 100 % only the blurred wallpaper is left (the user's wish after seeing the grey glass in the colour themes). Win11 is unchanged. A fully transparent window without blur is not needed, and the bright white spot of the blobs look is dropped (both by the user). The slider previews at once and saves on release.
- Wallpaper veil (24f): works in every theme (the user's wish), its colour follows the theme tint.
- Tray (25a): X hides the window to the tray, exit only through the tray menu (variant A, chosen by the user). Closing is cancelled by the window's closing event; if the window cannot be hidden, closing is allowed so the user is never trapped. pystray and pillow live in requirements-local.txt only (CI stays light). The tray icon is a drawn blue circle for now. The minimize button is unchanged until the island is designed (25b).
- Island (25b): built and checked on its own first, wired in later (the user's decision after a long failed attempt in an earlier chat). tkinter was tried first and dropped (no smooth edges, no glow); the island is now Qt (PySide6) in a separate process, chosen by the user after comparing Qt with an HTML window (the user: "I want the best, many ideas later"). The main window stays on PyWebView. Always visible for now (variant A, chosen by the user).
- Island look and text (25b-5/6, user): no glow, minimal, like the window; colours follow the window theme (all four themes); the answer text is shown (up to two lines) and disappears 1.5 s after she stops speaking; the minimize button stays as it is; "always visible" for now; the text mode and the attachment style go to the settings later; the dot will be replaced later.
- Island wave (25b-7, user): the bottom edge of the island is wavy and always moves (also in idle); the
  idea comes from the Island app (closed source, only ideas, no code or art copied). First without
  sound; the microphone loudness channel ("level") is a separate later stage. The characters in
  place of the dot (eyes etc.) and event cards were offered and are postponed.
- Text reveal (26c, user): replies without speech and chunks not found in the text are shown whole /
  ignored; the hide timer (1.5 s after SPEAKING ends) stays as it is.
- Island on Qt Quick (28, user): moved from QWidget paintEvent to Qt Quick (QML Shape, D3D11, frame-synced) after a probe showed
  working transparency and frames matching the monitor rate; logic stays in Python and is tested, QML only draws.
- Island icon (29, user): a choice of looks like the circles; eyes and equalizer first, a third look of the
  user's own comes later (he will describe it). The dot stays the default.
- Island icon blobs (30, Claude on the user's "решай сам"): soft circles with a radial gradient, not a real
  blur (a blur effect could bring the jitter of stage 28 back); one colour like the other looks, a
  two-colour variant is possible later. The user checked it live and is happy.
- My Wave by mood (14): a separate handler "wave_mood" before "wave" in the chain (variant A, chosen by
  Claude on the user's "делай как лучше"); a phrase without a mood returns None and goes on to the
  plain wave handler. Chain by state: other mood selected -> reset, open the panel, press the mood,
  check the button state and playback, close the panel. The same mood while playing -> "already
  playing"; the same mood on pause -> reset and choose again.
- Island accent (31): only the icon in idle and loading takes the Windows accent, other states keep their colours, like in the window (variant A, chosen by the user); loading was added by Claude so the start does not jump. Only the win11 theme.
- Wave cards (32): always start the best matching card, no questions (user). Tie: shorter title,
  then the card listed first.
- Wave cards overlap with the plain wave (variant A, chosen by the user): try the card first; if
  nothing was pressed and the phrase is a plain wave request, start the plain wave. Accepted cost:
  a missing card in "включи мою волну <name>" silently starts the plain wave.
- 32d (search fallback) postponed by the user; the voice command (32e) was built first.
- Window appearance (33, user): variant "A3": the whole window dissolves in at start and from the tray
  and dissolves out on X. The early taskbar icon stays (variant A).