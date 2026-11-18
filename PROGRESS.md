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

  - [x] Stage 7a-7b: Yandex Music track search, 220 tests
  - friday/ym_search_probe.py (diagnostic, live-checked), friday/music_search.py
    (TrackSearch: phrase -> one track or a status FOUND / NOT_FOUND / NO_TOKEN / ERROR;
    the token is never logged; client is created lazily and retried after an error)
  - Next: 7c (start the track), 7d (voice command "включи ...")

    - [x] Stage 7c: start a found Yandex Music track, 244 tests
  - friday/track_launcher.py (pure logic: SMTC check first -> ALREADY_PLAYING without
    opening the link; otherwise open link, wait for panel up to 15 s, compare title
    strictly (case, "ё", spaces ignored), invoke() play, confirm via SMTC;
    statuses STARTED / ALREADY_PLAYING / NO_PANEL / WRONG_TRACK / NOT_CONFIRMED / ERROR)
  - friday/playback_check.py (is the given track playing, via SMTC; tested),
    friday/ym_ui.py (UI Automation panel search; live-checked, no tests),
    friday/ym_launch_probe.py (live check: search + start)
  - Checked live: other track playing -> STARTED, same track playing -> ALREADY_PLAYING,
    paused -> STARTED, Music closed (cold start) -> STARTED in ~11 s
  - Next: 7d (voice command "включи ...")

- [x] Stage 7d: voice command "включи песню ...", 276 tests
  - friday/play_request.py (strict parser: play verb first, then песня / трек / композиция,
    the rest is the search query; "включи свет" is not a request; "включи песню" without
    a name stays the old "продолжить")
  - friday/play_handler.py (search -> launch -> spoken answer; never returns None for a
    recognized request; chain_handlers: play handler first, then music handler)
  - friday/voice.py wires TrackSearch(YM_TOKEN) + ym_ui.build_launcher()
  - Checked by voice: new track from closed Music (cold start) -> "Включаю ...",
    same again -> "Этот трек уже играет", "включи песню" -> "Продолжаю",
    "включи свет" -> LLM, pause / next / what's playing as before

- [x] Stage 7e: play a whole artist by voice, 315 tests
  - friday/artist_request.py (strict parser: play verb, then исполнитель / артист /
    певец / группа, then the name, up to 5 words)
  - friday/artist_search.py (ArtistSearch, same statuses as TrackSearch),
    friday/artist_playback.py (is this artist playing, via SMTC: the name is among
    the artists of the current track), friday/artist_handler.py (search -> launch ->
    spoken answer; chain order: play handler, artist handler, music handler)
  - friday/ym_artist_ui.py (UI Automation; live-checked, no tests), reuses TrackLauncher
  - friday/ym_artist_launch_probe.py (live check: search + start)
  - Checked live: other artist playing -> started, same again -> already_playing,
    page of another artist open -> started, Music closed (cold start) -> started,
    a track panel left open does not break it

- [x] Stage 8a-8c: long-term memory by voice commands, 419 tests
  - friday/memory_store.py (MemoryStore: facts in data/memory/facts.json, atomic save,
    broken file kept as .bad-<time>, limits 100 facts / 300 chars, fact texts never logged;
    forget matches by word stems, so "кошку" finds "кошка")
  - friday/memory_request.py (strict parser: the phrase must START with запомни / забудь,
    or be a short "что ты обо мне помнишь"; "забудь всё" is deliberately not a query)
  - friday/memory_handler.py (parser + store + spoken answer; never returns None for a
    recognized request; first in the command chain in voice.py)
  - Checked by voice: remember, repeat -> "Это я уже знаю", recall, forget, facts survive
    a restart, ordinary speech still goes to the LLM

- [x] Stage 8d: saved facts go to the LLM system prompt, 428 tests
  - friday/memory_prompt.py (with_facts: facts appended to the persona prompt as data,
    not instructions; newest kept when over 2000 chars)
  - Assistant accepts system_prompt as a string or a function called every turn, so a fact
    saved by voice works at once (voice.py passes a lambda with memory.facts())
  - Checked by voice: name from memory, a new fact works without restart, small talk does
    not recite the facts, unknown facts are not invented

- [x] Stage 8e: "забудь" also clears the dialogue history, 434 tests
  - memory_handler: optional on_forgotten callback, called only when a forget request
    really removed facts (not on remember / recall / nothing found); a broken callback
    does not break the spoken answer
  - voice.py creates one ConversationHistory, gives it to Assistant and passes
    history.clear as on_forgotten
  - Bug fixed: Assistant did `history or ConversationHistory()`, and an empty history is
    falsy (it has __len__), so a history passed from outside was silently replaced.
    Now `history if history is not None else ...`
  - Checked by voice: remember name -> forget -> "не знаю" without a restart

- [x] Stage 9: "включи мою волну" by voice, 470 tests
  - friday/wave_request.py (strict parser: the word "моя/мою" + "волна", a play verb unless
    the phrase is just "моя волна"; "по настроению", "для тренировки", "что такое моя волна"
    are not hijacked)
  - friday/wave_launcher.py (pure logic: SMTC check first -> ALREADY_PLAYING; otherwise find
    the wave player, press, confirm via SMTC; statuses STARTED / ALREADY_PLAYING / NO_PLAYER /
    NOT_CONFIRMED / ERROR), playback_check.make_is_any_playing (is anything playing in Music)
  - friday/wave_ui.py (UI Automation; live-checked, no tests), probes ym_wave_probe.py and
    ym_wave_press_probe.py
  - friday/wave_handler.py (status -> spoken answer; never None for a recognized request);
    voice.py chain order: memory, wave, play, artist, music
  - Decision (variant A, "выбери сам"): if the wave page is not open, Friday only says so
    ("Открой Мою волну в приложении"); opening it through the menu is a separate later stage
  - Checked by voice: started, already playing, "Моя коллекция" -> not found and nothing
    pressed, "включи свет" goes to the LLM, song / next / pause as before

- [x] Stage 10a: vision probes, 490 tests
  - friday/vision_probe.py (does a provider accept an image: solid red PNG, "what color"),
    friday/vision_shot_probe.py (real screenshot, 3 widths, 3 Cloudflare models; Pillow is
    imported lazily)
  - Live results (Belarus, no VPN): cf-mistral reads the screen well, 4.1 / 5.0 / 6.3 s at
    1024 / 1536 / 1920 px. cf-llama4-scout reads it too but takes 21-32 s and adds markdown and
    LaTeX; at 1024 px it misread small URL-bar text ("neuromachine" vs "neuromachina"), at 1536
    it was right. cf-gemma4 returns empty content at every size (cause not checked, probably it
    spends the token budget on reasoning). OpenRouter free gemma: HTTP 429 every time.
  - Decisions: full screen first (user's choice), capture takes an optional target (rectangle,
    window) later; screenshot downscaled to width 1536, JPEG q85 (~190 KB), configurable; chain
    cf-mistral -> cf-llama4-scout -> OpenRouter, gemma4 excluded; the voice prompt asks for a
    short plain-text answer, no markdown. Screenshots go to the cloud: add a privacy note to the
    readmes when the stage is done.
  - Pillow moved to requirements.txt (light, CI tests the image logic); chosen by Claude on the
    user's "делай как лучше". Use Image.Resampling.LANCZOS, not Image.LANCZOS (Pylance flags it).
  - Next: 10b screen capture, 10c vision client, 10d voice command ("что на экране")

- [x] Stage 10b: screen capture, 502 tests
  - friday/screen_capture.py: capture_screen(grab=grab_full_screen, max_width=1536,
    quality=85) -> Screenshot(data, mime, width, height, source_width, source_height).
    The grabber is injected, so a rectangle or a window grabber can be added later without
    changes. Errors become ScreenCaptureError; bad settings raise ValueError before grabbing.
  - Checked live: 1920x1200 -> 1536x960, ~267 KB, 87 ms, image is whole and readable.
  - Open point: SetProcessDpiAwareness is process-wide; inside the running assistant (PyWebView
    already started) it may not apply. Check in 10d via the log line "screenshot WxH -> WxH".
  - fit_size is duplicated in vision_shot_probe.py (the probe); remove when the probe goes.
  - Next: 10c vision client (chain cf-mistral -> cf-llama4-scout -> OpenRouter, longer
    timeout than text, plain-text prompt), then 10d voice command "что на экране".

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
- Yandex Music tracks: the link `yandexmusic://album/<id>/track/<id>` (from a share link)
  only opens the track page, it does not play. UI Automation `invoke()` on the track
  panel's "Воспроизведение" button starts the track without mouse movement. The page has
  two big identical buttons (album vs track panel; all have name "Воспроизведение" and
  empty id), so never pick one by name or size alone.
- Reliable anchor for the track panel button: the container (Custom) that holds a
  "Закрыть" button, a "Трек" text and the track title text; the right button is the
  "Воспроизведение" inside it. Compare the title with the requested track before clicking.
- Window visibility: opening the link brings the window to the front by itself, also when
  it was fully covered or minimized. A half-covered window still exposes its elements.
  A window that stays fully covered gives 0 candidates, so always open the link first.
- The panel button toggles: check SMTC first, do not click if the track already plays.
- Console noise (ERR_FAILED, "Unable to move the cache") comes from the second app launch
  done by `os.startfile`; it is harmless, hide it in the module.
- Yandex Music search (yandex-music 3.2.2, YM_TOKEN in .env) works from Belarus without a VPN.
  `client.search(text, type_="track")` returns up to 20 tracks. The first result was the
  right track for "Полетели Киркоров", "Till I Collapse Eminem" and the Whisper-style
  "тил ай коллапс эминем" (Yandex handles transliteration). Second hit can be an
  "Instrumental" version, so skip those. `artist.name` can be None. The same track id can
  come with different album ids; link: `yandexmusic://album/<album_id>/track/<track_id>`.
- Track panel in the UI tree: the play button lives in a Custom container with "Закрыть"
  and the title; the container also holds a List of similar tracks, each row with its own
  "Воспроизведение" button. ym_ui.py counts only the buttons outside nested Lists.
  While a track plays, the panel button is named "Пауза", so find_panel() finds nothing:
  always ask SMTC first.
- Cold start of Yandex Music takes ~10 s before the panel appears; panel_timeout is 15 s
  (set in ym_ui.build_launcher, not in the TrackLauncher default of 6 s).
- Strict title match: "Название (версия)" on the panel will give WRONG_TRACK; relax only
  if it happens live.
- Known weak spot: SMTC only reports the title, so another track with the same title
  counts as ALREADY_PLAYING.
- Console output of ym_* probes with `> file` is cp866 (mojibake in the file only).
- Track launch runs in the TurnRunner worker thread; UI Automation and SMTC work there.
- Whisper adds commas and stray words ("полетели и Киркоров"); Yandex search tolerates it.
- A bare "Дальше." (no music word) is not a command and goes to the LLM, by design.
- Artist page in the UI tree: the page title in the Document and the big name heading
  are NOT reliable (the title can stay "Яндекс Музыка — ..."). The artist is identified
  by the most frequent "Артист <name>" link in the container; a tie means unknown.
- The container with the "Исполнитель" mark holds two play buttons once the new release
  is out (yellow "Слушать" first in tree order, release cover button after it); before the
  release the cover button is named "Для воспроизведения нужно дождаться предстоящего
  релиза". ym_artist_ui takes the first own button and checks its position.
- While an artist plays, the button is named "Пауза": ask SMTC first (artist name is
  matched as a substring of the track's artists).
- Whisper mistakes lead to a similar-sounding artist ("дурак дураком" -> "дурак"); the
  spoken "Включаю <name>" lets the user notice. A track panel opened on top of the
  artist page used to be a worry, it is not.
- A play phrase for an artist needs a marker word (исполнитель / артист / группа);
  bare "включи Киркорова" is not a command, by design.
- ArtistLauncher.launch(link, title) keeps the parameter name "title" to match the
  Launcher protocol; there "title" is the artist name.
- Whisper can spell a place or name differently from the user ("Мозыр" -> "Мозер"). A fact is
  stored as heard, so "забудь про Мозыр" will not find it; recall first, then forget by a
  word that was heard correctly.
- Facts are sent to the cloud LLM providers inside the system prompt on every turn. They stay
  in data/memory/facts.json locally (git-ignored); do not dictate secrets to Friday.
- My Wave player block: a Group whose direct children hold exactly two Sliders and at least
  three Buttons, middle of the last three = Play. Structure alone is NOT enough: on "Моя
  коллекция" the bottom bar matches too (queue / sound settings / mute), and one live run
  pressed "Настройки звука". So wave_ui presses only a middle button named "Воспроизведение".
  While music plays the button is named "Пауза": ask SMTC first, never press.
- Wave not confirmed through the menu path: "Моя волна" menu item (Hyperlink, 240x60 in the
  "Главное меню" group) would need a name lookup, which conflicts with the structure-first rule.


## Next
Pick the next stage: wake word "Пятница", screen vision, or My Wave extras (open the wave
page through the menu, wave by mood / for an activity).