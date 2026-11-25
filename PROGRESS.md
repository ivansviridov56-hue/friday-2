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
  - fit_size was duplicated in vision_shot_probe.py; the probe was removed in stage 14a.
  - Next: 10c vision client (chain cf-mistral -> cf-llama4-scout -> OpenRouter, longer
    timeout than text, plain-text prompt), then 10d voice command "что на экране".

- [x] Stage 10c: vision client, 510 tests
  - friday/llm.py: ask() takes optional keyword-only timeout and max_tokens (defaults stay 15 s / 300,
    so the text chain is unchanged); the limits apply to every provider in the fallback.
  - friday/vision.py: VISION_CHAIN (cf-mistral -> cf-llama4-scout -> or-gemma, gemma4 on Cloudflare
    excluded), build_messages (system prompt asks for 2-3 short plain-text sentences in Russian, no
    markdown; screenshot goes as a data URL), describe(client, screenshot, question) with a 30 s timeout
    and 400 tokens, build_vision_client(). describe() accepts any object with ask() (Asker protocol).
  - Not checked live yet: the whole path (capture -> describe) on a real screen.
  - Next: live check of 10c, then 10d voice command "что на экране" (say "Смотрю экран" first,
    the answer takes 6-23 s; ask the user), then privacy note in both readmes.

- [x] Stage 10d: voice command "что на экране", 541 tests
  - friday/screen_request.py (strict parser: the word "экран" is required; the phrase must start
    with "что ... на экране" or with "посмотри" / "опиши"; up to 7 words after fillers;
    "выключи экран", "что такое экран", "запомни, что на экране ..." are not hijacked)
  - friday/screen_handler.py (capture -> "Смотрю экран." spoken in a background thread while the
    vision model works -> answer; the answer waits for the announce to finish, so there is no
    overlap; never None for a recognized request: capture error, all providers failed and any
    other error each get a spoken answer; a broken announce does not break the answer)
  - voice.py: handler goes after the memory handler (so "запомни ..." always reaches memory);
    one vision client per run; the heard phrase is the question for the model
  - Decisions (chosen by Claude on the user's "выбери сам"): announce phrase, strict phrase
    filter, question = heard phrase, parallel announce.
  - Checked by voice: both phrases recognized, "включи свет" and "что такое экран" go to the LLM,
    pause / next as before. Screenshot inside the running assistant is 1920x1200 -> 1536x960,
    so the DPI open point from 10b is closed. Answer was truthful (editor, file tree, desktop
    picture). The model took the user's own chat line "Что на экране?" for a button in the
    assistant window (the window is in the frame; known quirk, harmless).
  - Open point: the answer was 4 sentences and spoke for up to 19 s; a new phrase is ignored
    meanwhile. The user left it as is. If it bothers: shorten SYSTEM_PROMPT to one or two short
    sentences and set VISION_MAX_TOKENS = 250.
  - Next: pick the next stage.
  - Stage 10 is done: privacy note added to both readmes.

- [x] Stage 11a: wake word probe, 556 tests
  - friday/wake_probe.py (live probe: 12 short clips with the name said six ways, then 45 s
    of speech without it; heard_name matches by the stem "пятниц"; Recorder and SpeechToText reused)
  - Results: name found in 10 of 12 clips. Misses: "Ветница" (quiet, lost first letter) and
    "Пятенца" (normal voice); both when the name stood alone. 6 of 6 with the name inside a
    phrase (start, middle, end). No false alarm on 45 s of ordinary speech.
  - Conclusion: stem match is not enough; fuzzy matching is needed. Open question for 11b: how to
    listen continuously (A: Whisper on short chunks with a voice detector; B: a small dedicated
    keyword model; C: keep only push-to-talk).
  - Decision (user, "ну наверное пока вариант А"): listen continuously with Whisper on short chunks
    plus a voice detector; the user expects to revisit this later (GPU load, privacy: everything
    the microphone hears is transcribed locally, only the phrase after the name goes to the cloud).
  - 11b: friday/wake_word.py (fuzzy match: similarity >= 0.7 and word length 5-9; "Ветница" and
    "Пятенца" match, "пятнадцать", "пятно", "пятка" do not).
  - Next: 11c continuous listener (chunking, voice detector, cut the phrase by a pause), then
    11d wiring into voice.py and the window indicator. X2 push-to-talk stays.
    - Decisions (user: "делай так как лучше"): after the name alone, wait for the next phrase up to
    6 s (window state "listening"); the listener transcribes a phrase to look for the name and the
    assistant transcribes it again (about 0.5 s extra), accepted for now, no change to assistant.py;
    a ready-text entry (handle_text) is a possible later optimization.

- [x] 11c-1: friday/speech_segmenter.py (continuous stream -> phrases by pauses: energy based,
    noise floor measured in the first 0.3 s and adapted during silence, 0.3 s of pre-roll, pause
    0.8 s ends a phrase, sounds under 0.3 s of speech dropped, phrase cut at 12 s), 598 tests.
    Thresholds (min_rms 0.012, noise factor 3) are tuned on synthetic audio only: they need a live
    check on the real microphone. Known weak spot: a background louder than speech (fan, TV).
  - Next: 11c-2 a way to subscribe to the microphone stream in recorder.py (tests in
    test_recorder.py), 11c-3 level probe on the real microphone, 11c-4 listener logic
    (segmenter + STT + wake_word + waiting for the command; muted while the assistant is busy,
    so she does not hear herself), then 11d wiring into voice.py and the window.

- [x] 11c-2: Recorder.add_listener / remove_listener (every audio frame goes to subscribers, also
    when no push-to-talk recording is going; called from the audio thread, so a listener must only
    queue the frame; a broken listener is logged and does not break the stream or other listeners),
    604 tests.
  - Next: 11c-3 live probe on the real microphone (levels of silence / speech and what the segmenter
    cuts out), then 11c-4 listener logic.

- [x] 11c-3: friday/mic_level_probe.py (live probe: 5 s of room background, 12 s of speech through
  Recorder.add_listener, levels, threshold, phrases found by the segmenter, one-line verdict), 621 tests.
  - Verdict fixed after the first live runs: speech is judged by its 90th percentile (pauses no
    longer count against it), a dead microphone is reported separately, a noisy background is a
    warning, not a failure.
  - SpeechSegmenter default min_rms lowered 0.012 -> 0.004 (shared constants DEFAULT_MIN_RMS,
    DEFAULT_NOISE_FACTOR).
  - Live numbers (lavalier, laptop). Quiet room: background 0.0001, speech p90 0.022, 3 phrases
    of 2.5-2.9 s found, none in silence (OK). Music on: background median 0.005, p95 0.02, 10% of
    silence frames above the threshold, one false 2.5 s phrase in silence. Another run (conditions
    not confirmed): background median 0.0004, 2.4% above the threshold, no phrases in silence, but
    the speech came out as ONE 10.1 s phrase (pauses never reached 0.8 s of quiet).
  - Next: 11c-4 listener logic.

- [x] 11c-3b: wake phrase must START with the name, 640 tests
  - Decision (chosen by Claude on the user's "выбери сам"): the name must start the phrase, after at
    most two lead-in words (эй / слушай / привет / ну ...). friday/wake_word.py: split_wake_phrase(text)
    returns the text after the name, "" for the name alone, None if the phrase does not start with the
    name ("в пятницу поедем" and "включи музыку, Пятница" do not wake her; X2 stays for those).
  - Music finding (the user confirmed: music was playing, pauses were made): the speech came out as ONE
    10.1 s phrase, so the energy segmenter does not find the end of a phrase over loud or dynamic music.
    Not patched blindly: the live listener (11c-4) will log phrase lengths and what Whisper heard, and
    we decide on real data (smarter end detection, name listening only without music, or a dedicated
    keyword model). SpeechToText.transcribe uses vad_filter=True, so music-only fragments should come
    back empty and cost little (to be confirmed live).
  - Next: 11c-4 listener logic (queue off the audio thread, segmenter, STT, split_wake_phrase, wait up
    to 6 s for the command after the name alone, silent while the assistant is busy or X2 is held,
    measurement log). Planned: off by default, switched on by an .env flag until it proves itself.

- [x] 11c-4: continuous listener, 666 tests
  - friday/wake_listener.py (WakeListener: frames from Recorder.add_listener -> queue -> worker thread ->
    SpeechSegmenter -> STT -> split_wake_phrase. Text after the name goes to submit(text) as a ready
    command; the name alone arms a 6 s wait for the next phrase (judged by when the phrase STARTED, and
    the wait does not expire while the user is speaking); deaf while is_busy() (assistant answering or
    X2 held) and for 1 s afterwards so she never hears herself; events "wake" / "command" / "timeout"
    for the window. Phrase texts are not logged unless log_text is on; the log has lengths and timings.)
  - Assistant.handle_text(text): the same turn from an already recognized phrase (no second STT).
    Reason: commands like "запомни ..." and "включи песню ..." must START with their verb, so the name
    cannot be left in the text; the listener passes the text after the name.
  - Not wired yet (11d): voice.py, TurnRunner accepting text, window states for wake / timeout,
    an .env flag to turn the listener on (off by default), the log_text debug flag.
  - Next: 11d wiring and the live check with music playing (see the music finding above).

- [x] 11d: wake listener wired into voice.py, off by default, 689 tests
  - voice.py: WAKE_WORD=1 in .env turns the listener on (WAKE_DEBUG=1 prints what Whisper heard:
    everything said near the microphone, for tuning only); one SerializedTranscriber shared by the
    listener and the assistant (one recognition at a time); TurnRunner takes text as well as audio
    (X2 still sends audio); is_busy = assistant answering or X2 held.
  - friday/wake_setup.py (env_flag, WakeIndicator: "wake" -> LISTENING, "timeout" -> IDLE, "cancel" and
    "command" leave the window to the assistant / X2; SerializedTranscriber). Event "cancel" added to the
    listener for the case when the assistant or X2 takes over during the wait.
  - Live check, quiet room, lavalier, no music: name + command in one phrase works; name alone + next
    phrase works; name alone + 7 s silence -> timeout; "мы поедем в пятницу на дачу" and phrases without
    the name do not wake her; her own voice was never heard back; short noises give 1.7 s phrases with
    empty text that Whisper's VAD rejects in 0-15 ms. Once Whisper heard "Тони Стах" for "Тони Старк"
    (recognition accuracy, not the listener).
  - Not yet checked: music playing; X2 together with the listener; the window indicator;
    speakers vs headphones.
  - Live check with music: see 11e.

- [x] 11e: why a phrase ended (diagnostics), level dump probe, README privacy note, 703 tests
  - SpeechSegmenter.last_end (EndInfo: reason "silence" or "max", threshold, floor); the listener
    logs "ended=... floor=... thr=..." next to every phrase. Old fakes without last_end still work.
  - friday/level_dump_probe.py: 48 s scenario with music, writes one RMS number per 30 ms plus step
    marks to data/probes/ (no sound, no words). Offline replay of the real segmenter on that dump:
    a 10 s music phrase closed by a pause, short phrases in quiet, no 12 s cuts. The earlier 12.0 s
    phrases came from steadier, louder music (the energy detector finds no 0.8 s pause there).
  - Live check, speakers, own music, user singing along: about 25 phrases, only one ended=max (12.0 s,
    singing over the track), the rest ended=silence. Over music: "Пятница, что играет", "Пятница,
    пауза", name alone + "следующая песня", "Пятница, как дела?" all worked; no false wake-ups; her
    own voice through the speakers was not heard; X2 works with the listener on (checked earlier).
  - Observed: Whisper hallucinates "Субтитры сделал ..." on non-speech (harmless without the name);
    the name was missed once of about 6 ("Ветнится"); at the start with loud music the threshold was
    0.0057-0.0078 (noise floor measured in the first 0.3 s) and fell back to 0.004 in quiet.
  - Decision: no smarter cut at the 12 s limit for now (rare in the live run).
  - Found, not wired to this stage: Edge TTS often fails with NoAudioReceived; retries make an
    answer take 5-10 s and some chunks are never spoken (latin names, short chunks).
  - README (en, ru): wake word feature line and privacy note for the always-on listening.
  - Next: fix the TTS NoAudioReceived problem (stage 12).

- [x] 12: Edge TTS failures and a local fallback voice, 729 tests
  - Problem: Edge TTS answers NoAudioReceived for some phrases (about 30% in a probe, more in live
    use). friday/tts_probe.py (python -m friday.tts_probe [rates]) showed it is NOT caused by parallel
    requests (1 vs 2 at a time: the same 6 of 20), the speaking rate (+0% vs +30%), the final period
    or the library (edge-tts 7.3.1 is the latest). Some phrases fail every time, others at random;
    a second try recovered about 1 of 8.
  - friday/tts_fallback.py: the Windows voice "Microsoft Irina Desktop" through PowerShell
    (System.Speech). The text travels in a base64 environment variable, never in the command line;
    returns WAV bytes; the temp file is deleted at once.
  - tts.py: one Edge try (RETRY_ATTEMPTS = 1), then the local voice for that chunk; if it fails
    too, the chunk is skipped (the answer stays in the window). speak_text passes the fallback,
    speak_async has none by default. audio.py plays mp3 or WAV (audio_kind).
  - Live check: a failed chunk is voiced by Irina after about 3.8 s (6.6-7.5 s with two Edge tries);
    Edge takes 1.2-2.4 s when it works. Irina's speed is fine. Both voices alternate in one answer.
  - Open: the cause is on the service side. A second cloud voice or a good local Russian voice
    would remove the voice change.
  - Seen in the log, not fixed: "что играет" heard as "стойграет" went to the LLM instead of the
    music command; "включи мою волну" with Yandex Music closed went to the LLM.

- [x] 13a: music commands tolerate Whisper mishearings, 752 tests
  - music_commands.py: a single unknown word of 7-20 letters is cut into two ("стойграет" ->
    "сто" + "играет"); a "?" stem ignores the first letter ("йграет", "играется"); aliases
    "што" / "шо" / "чо" / "сто" -> "что"; "что играют" is a command too. Whole-phrase fuzzy
    matching was measured and rejected (too little margin against ordinary talk).
    Lookalikes ("во что играем сегодня", "он играет на гитаре", "сто рублей", "заиграет") stay
    ordinary speech (tests/test_music_commands_fuzzy.py).
  - Checked by voice (quiet voice, music on, wake word on): "что играет" in three spellings and
    two next-track phrases worked, "ты самая лучшая" went to the LLM. The glued "стойграет" did
    not occur live, it is covered by tests only.
  - Not done: Whisper hints (initial_prompt / hotwords): risky in an always-on listener
    (hallucinated words, false wake-ups); try only if mishearings stay frequent.
  - Not checked: "включи мою волну" with Yandex Music open.
  - Seen in the log, not fixed: "Включаю следующий." is a masculine form (window text only).
    Edge synthesis took 5.7-6.1 s for two chunks of one answer (service side, no fallback
    triggered because Edge did not fail, only slow).

- [x] Stage 13b: My Wave works with a minimized Yandex Music window, 755 tests
  - friday/voice.py: the My Wave handler was dropped from chain_handlers in stage 10d
    (voice.py has no unit tests, so nothing caught it); put back after the screen handler.
  - friday/wave_launcher.py: optional `prepare` hook, called once before the player lookup
    when nothing plays yet (a failing hook is swallowed); tests/test_wave_launcher_prepare.py.
  - friday/window_restore.py: restores minimized windows of the Yandex Music processes through
    Win32 (EnumWindows by pid, IsIconic, ShowWindow SW_RESTORE); live-checked, no unit tests.
  - Checked by voice (wake word on): minimized -> restored and "Включаю Мою волну" (3 of 3),
    already playing -> "Музыка уже играет" without touching the window.
  - Not done: Music fully closed or hidden in the tray still gives "Открой Мою волну в
    приложении" (that is variant C).

- [x] Stage 13c: the Yandex Music window is minimized back after My Wave starts, 761 tests
  - friday/wave_launcher.py: optional `after_start` hook, called only when the wave really
    started (STARTED); a failing hook is swallowed; tests/test_wave_launcher_after_start.py.
  - friday/window_restore.py: restore_minimized returns the restored window handles,
    minimize_windows puts exactly those windows back; if nothing was restored, the log has
    "restore: windows seen: ..." (only visibility / minimized / has-title flags, no titles).
  - friday/wave_ui.py: _WindowRestorer remembers the windows it restored; a window that was
    already open stays as it is.
  - Checked by voice (wake word on): minimized -> restored, wave started, minimized back
    (3 of 3); already playing -> "Музыка уже играет", window untouched.
  - Not reproduced: an earlier run where 7 processes were found but no window passed the
    filter. If it comes back, read the "windows seen" log line.

- [x] Stage 13d: the command chain is built in one place, 768 tests
  - friday/command_chain.py: COMMAND_ORDER = memory, screen, wave, play, artist, music;
    build_command_chain(handlers) takes a name -> handler dict and raises ValueError if a
    handler is missing or unknown (the case that hid the lost My Wave handler in stage 10d)
  - friday/voice.py calls build_command_chain instead of chain_handlers
  - Checked by voice (wake word on): wave, what's playing, play a song, screen, memory

- [x] Stage 13e: My Wave when Yandex Music is closed, 775 tests
  - friday/wave_launcher.py: optional is_running / open_wave / cold_start_timeout (20 s);
    only when no Music process exists, the link yandexmusic://radio/user/onyourwave is opened
    and the launcher waits longer for the player; without these parameters nothing changes
  - friday/wave_ui.py: build_launcher passes is_running (process list) and open_wave
    (WAVE_LINK through ym_ui.open_link)
  - Checked by voice (wake word on): closed Music -> wave starts in ~4 s, window stays in front;
    Music open on another page -> "Не вижу плеер Моей волны..."; already playing -> "Музыка уже играет"

- [x] Stage 13f: local Silero voice as the main TTS, 798 tests
  - friday/tts_silero.py (SileroVoice: model v5_ru, speaker kseniya, 48000 Hz, CPU, lazy torch import,
    loader injected for tests, warm_up(), returns WAV bytes; a load or synthesis failure is a SileroError
    and a failed load is retried on the next call), friday/tts_choice.py (choose_tts: TTS_ENGINE
    "silero" by default, "edge" keeps the old Edge + Windows fallback path, unknown name raises
    ValueError at startup), tts.py: speak_async / speak_text take an optional `engine`; with it every
    chunk is voiced by it and Edge is not used, one failed chunk does not silence the rest.
  - voice.py: choose_tts(os.environ.get("TTS_ENGINE")), warm-up in a background thread started before
    Whisper loads, engine passed to speak_text. .env.example has TTS_ENGINE, requirements-local.txt has
    silero>=0.5 (torch 2.15.0+cpu comes with it), .gitignore has latest_silero_models.yml (the silero
    package writes it into the working directory on every model load).
  - Tests: 775 + 11 (tts_silero) + 3 (tts_engine) + 9 (tts_choice) = 798 passed.
  - Checked by voice (wake word on, Silero): model loaded in 15.6 s (in parallel with Whisper), synthesis
    33-125 ms per chunk, first chunk ready in 43-112 ms (Edge: 1.2-2.4 s); Edge and Irina were never
    called. Wave, what's playing, play a song by name, pause, continue and the wake word all work as before.
  - Seen, not investigated: in a multi-chunk answer "chunk 2/3 ready" comes 1.5-2.4 s after chunk 1
    (looks like waiting for the previous chunk to finish playing, not slow synthesis); a harmless
    TypedStorage UserWarning from torch at model load; the wake listener cut several phrases at 12 s
    (ended=max) in this run.
   - Startup window: on the second live run Silero loaded in 4.7 s (the first run: 15.6 s, cold disk cache)
    and finished before Whisper, so the window where the voice is not ready was not reproduced. In code a
    phrase that arrives during loading waits on the load lock and the model is loaded once (covered by
    test_phrase_during_loading_waits_and_loads_only_once).
  - Licence: Silero models are CC BY-NC (non-commercial), except the base CIS models under MIT, and
    v5_ru is not one of them. The model is never committed; both readmes carry the note and point to
    TTS_ENGINE=edge for commercial use. The licence of the `silero` pip package itself was not checked.

- [x] Stage 13g: Latin words are spelled in Cyrillic before Silero, 811 tests
  - Problem: the Russian Silero model silently skips Latin letters, so "Python" or "GitHub" were not spoken.
  - friday/translit.py: latin_to_cyrillic(text) replaces every Latin word; a small dictionary of common
    names first (Yandex, Music, Python, GitHub, Windows, YouTube), then a letter-by-letter fallback with
    digraphs (sh, ch, zh, kh, ph, ts, ck); case is kept (first capital, ALL CAPS). Russian text, digits
    and punctuation are untouched.
  - tts_silero.py: synthesize() passes the converted text to the model; the window and dialogue history
    keep the original text. The Edge path is not changed.
  - Tests: 798 + 11 (translit) + 2 (tts_silero) = 811 passed.
  - Checked by voice: "Python" and "GitHub" sound fine.
  - Decision (user: "сделаем так, а дальше посмотрим"): variant A (spelling in Cyrillic, one voice); a
    separate English voice or Edge for Latin chunks was not chosen.
  - Not done: the dictionary is short; add words as they are found live. The fallback gives only a rough
    pronunciation.

- [x] Stage 14a: removed friday/vision_shot_probe.py and its test (the fit_size duplicate), 800 tests
  - The probe was a one-off diagnostic from stage 10a; its results stay in the 10a notes above.
  - fit_size lives only in friday/screen_capture.py now.

- [x] Stage 15a: new window look after the old project's design, 808 tests
  - friday/ui/ is split into index.html (markup), styles.css (theme, circles, bubbles) and app.js
    (window.fridayUi.setState / addMessage, same API as before, so ui_bridge.py and window.py are
    unchanged). Only the look of the old project was reused, none of its logic.
  - Dark navy theme; four blurred circles on the right morph and "breathe"; their colour follows the
    state through a body class state-<name>: idle blue, listening red-pink, thinking violet,
    speaking cyan, loading blue (faster), error red. Bubbles: user gradient with a glow,
    assistant dark card.
  - tests/test_ui_assets.py (8 tests): every State has a CSS rule, the page links its assets,
    app.js exposes the bridge API.
  - Checked live in the demo window (python -m friday.window): looks fine.
  - Not done: the left strip with the logo, window controls (a frameless window), a text input,
    circles reacting to the sound level (the old project did it through requestAnimationFrame).

- [x] Stage 15b: circles react to the microphone loudness, 834 tests
  - friday/level_meter.py (LevelMeter: RMS of the frames, noise gate 0.004, full 0.05, averaged,
    attack/release smoothing, at most 20 values a second; pure logic, no threads)
  - friday/level_publisher.py (LevelPublisher: Recorder.add_listener only queues frames in the audio
    thread, a worker thread computes and publishes LevelChanged; values go out only in the LISTENING
    state, one zero when listening ends)
  - ui_events.py: LevelChanged (not remembered by the bus); ui_bridge.py: window.fridayUi.setLevel(x),
    dropped (not queued) before the page has loaded
  - ui: app.js eases the level every frame (factor 0.12) into the CSS variable --lvl; styles.css scales the
    circles by it (inner circles more than outer). The per-state breathing speed (--breath) was removed:
    it made the circles jump when the colour changed.
  - voice.py creates LevelPublisher next to the Recorder and closes it in finally.
  - Checked live: circles follow the voice, colour change is smooth now, 160+ fps. Easing 0.25 felt
    too sharp, 0.12 is fine.
  - Not done: her own voice (speaking state) does not move the circles (variant B: needs a loudness
    envelope of the answer synchronized with playback).

- [x] Stage 16: text input in the window, 853 tests
  - friday/text_input.py (TextInput: strips the text, rejects empty text, text over 500 characters, and
    text typed before the assistant is ready; the handler is set by the assistant thread when it is
    ready and cleared on exit; the typed text is never logged; WindowApi.submit_text is the only method
    the page can call, and it accepts only strings)
  - window.py: run_window takes an optional api and passes it to PyWebView as js_api; voice.py creates
    TextInput in main(), passes it to the assistant thread and hands it runner.submit (the same path as a
    phrase from the wake listener, so music and memory commands work from typed text too; no
    ListeningIndicator, it belongs to the mouse button)
  - ui: a simple pill-shaped field with a round send button under the chat (index.html, styles.css,
    app.js); on refusal (busy or loading) the field flashes red and keeps the text; no new window design
    yet
  - Tests: 850 + 3 (test_ui_composer: elements, API call, styles) = 853; test_text_input has 16
  - Checked live: typed question answered and spoken, "что играет" works, typed phrase while she answers
    is refused (field flashes red, text stays), empty field does nothing, X2 and the wake word as before.
  - Not done: showing a typed message before she answers is handled by the existing events (works);
    the look of the field is temporary and will change with the window design.

- [x] Stage 17: frameless window with its own buttons, 879 tests
  - friday/window_controls.py (WindowControls: minimize, close and resize callbacks bound by window.py
    once the window exists and cleared when it closes; sizes clamped to 320x420 .. 4000x3000; a broken
    callback does not raise), friday/window_api.py (WindowApi moved out of text_input.py: submit_text,
    minimize_window, close_window, resize_window; the whole public API is pinned by a test)
  - window.py: frameless=True, easy_drag=False, controls bound to window.minimize / destroy / resize;
    voice.py creates WindowControls next to TextInput and passes both to run_window
  - ui: only "minimize" and "close" buttons in the header (no maximize, by the user's choice); a drag
    strip with the class pywebview-drag-region under the header text; three invisible resize handles
    (right edge, bottom edge, bottom-right corner) drive window.resize through the API, one request at
    a time, so the last wanted size wins
  - Not possible: resizing from the left or top edge (it would also need moving the window)
  - Tests: 853 - 4 (the old WindowApi tests left test_text_input) + 6 (window_controls) + 6 (resize) +
    7 (window_api) + 5 (resize in window_api) + 4 + 2 (ui) = 879
  - Checked live: no system frame, drag by the header, minimize and restore, close without errors,
    resize by the right edge / bottom edge / corner (minimum respected), text input, X2.

- [x] Stage 18: window layout like the old project, 884 tests
  - ui: the chat is a column on the left (max 640 px), under it an "island": a pill-shaped glass input
    field (the send arrow, an SVG icon, appears only when there is text) and a small round music circle
    next to it (a placeholder styled like the old project's satellite: dark glass, thin teal ring;
    nothing is connected to it yet). Removed by the user's decision: the three dots and the hint under
    the field. No microphone button in the field (push-to-talk and the wake word stay).
  - A fine noise layer over the background (#bg-layer::after, opacity 0.01) hides colour steps; the
    blur of the circles is switched off (blur(0px) in styles.css, kept for experiments): a bigger blur
    made vertical stripes (banding) worse; a gradient-edge variant without blur was tried and looked worse
    too. The window default size is now 1000 px wide.
  - tests/test_ui_layout.py (5 tests).
  - Not done: the look of the circles will be reconsidered (maybe replaced by something else); the music
    circle should hide until music plays and show the cover (needs title and cover from SMTC); the black
    Windows-like theme and real Mica (not checked whether PyWebView on Windows can do a transparent window).

- [x] Stage 18b: input island
  - Text area grows with the text (up to 5 rows, then inner scroll). Enter sends, Shift+Enter adds a line.
  - Island is compact (260 px) and opens to 500 px on hover, focus, or while it holds text.
  - No state hints in the placeholder and no state glow (the user's decision). The only reaction is the nudge when a phrase is refused.
  - The island animates its own height; the text area jumps to its final height at once. The composer uses overflow: clip, so the caret cannot scroll the text.
  - Tests: 892 passed.
  - Known issue (postponed by the user): the text jitters slightly when typing fast with Shift+Enter. Cause is probably fitInput restarting the height transition on every keypress.

- [x] Stage 18c: input island tuned, take 7 in styles.css
  - Smaller (closed 220 px, open 400 px), slower opening (0.6 s, no spring), raised (44 px from the bottom).
  - Checked live: the user is happy with the size and the speed.

- [x] Stage 19a: music circle shows the cover of the current track, 910 tests
  - friday/smtc.py: SmtcSession.thumbnail_bytes() (live-checked), friday/ym_cover_probe.py (diagnostic: saves each session's cover to the temp folder)
  - friday/cover_data.py (bytes -> PNG / JPEG data URL), CoverChanged event in ui_events.py, UiBridge calls window.fridayUi.setCover(image or null)
  - friday/cover_publisher.py (polls every 2 s; reads the cover only when the track changes, retries while the cover is missing, publishes None when Music closes or has no track), friday/cover_source.py (SMTC adapter, live-checked, no tests)
  - UiEventBus remembers the last CoverChanged and gives it to a late subscriber, like the state
  - Window: #music-orb is hidden until a cover arrives, shows it round, stays on screen while paused, hides when Music closes; wired into voice.py next to LevelPublisher
  - Checked live: cover appears, track change swaps the cover, pause keeps the circle.

- [x] Stage 20a: switchable look of the background circles, 924 tests
  - friday/circles_style.py (CIRCLES from .env: classic / blobs / equalizer / dots; empty or unknown gives classic with a warning)
  - CirclesStyleChanged event in ui_events.py (the bus remembers the last one, like the state and the cover), UiBridge calls window.fridayUi.setCirclesStyle(name), voice.py publishes it at start
  - Page: friday/ui/circles/core.js (registry, eased state colours, loudness, canvas helper) and one file per look: blobs.js (CSS blurred spots), equalizer.js (canvas rays), dots.js (canvas particles). Classic stays in index.html / styles.css and is only hidden when another look is chosen. A new look = one new file + one script line in index.html
  - No flash of the old circles at start: .circles-anchor is hidden until body has data-circles
  - Checked live: all four looks work, colour follows the state, loudness moves them while listening. The user will tune each look later.

- [x] Stage 21a: colour themes of the window, 938 tests
  - friday/theme.py (THEME from .env: classic / windows / black; empty or unknown gives classic with a warning)
  - ThemeChanged event in ui_events.py (the bus remembers the last one and replays it first), UiBridge calls window.fridayUi.setTheme(name), voice.py publishes it at start
  - styles.css: the colours moved into variables (values of the classic blue theme, nothing changed visually); friday/ui/themes/windows.css (dark grey, no blue) and black.css (near-black) only override colours. Shapes, sizes and fonts are the same in all themes (the user's decision). A new theme = one new CSS file + one link line in index.html + a name in THEMES
  - The page stays hidden until a theme arrives (3 s safety net in app.js applies classic), so there is no colour flash at start
  - Checked live: all three themes work with all four circle looks.

- [x] Stage 21b: state colours for the grey themes
  - windows: pink / lilac / mint / orange-red, calm and slightly dusty; black: the same hues, brighter and more saturated; classic keeps the old colours. Set at the end of themes/windows.css and themes/black.css.
  - The user: "leave it like this for now" (may be tuned later).

- [x] Stage 22a: settings screen, 962 tests
  - friday/settings_store.py (data/settings.json, git-ignored; only known keys and values are read or written; a missing, broken or odd file gives an empty dict; atomic write), friday/settings_service.py (saved choice wins over .env, publishes ThemeChanged / CirclesStyleChanged, saves, a failed save still applies the choice)
  - WindowApi gets get_settings, set_theme, set_circles_style (strings only); the page can call nothing else (the guard test lists all page methods). voice.py builds the service and publishes the starting choices through it
  - Page: gear button in the header, panel on the right (theme and circles look as pill buttons, current one highlighted); the lists of allowed values come from Python, so a new theme or look appears in the panel by itself, only its label goes into the dictionaries in app.js. Closes by the gear, the cross or Esc
  - Checked live: the choice applies at once, survives a restart, and wins over .env.

- [x] Stage 23a-23c: Windows 11 theme with a real blurred window background, 980 tests
  - friday/backdrop_logic.py (pure: accent parsing, tint colour, build check, the "kick" steps; 17 tests)
  - friday/win_backdrop.py (Windows calls, live-checked, no tests): old undocumented acrylic through
    SetWindowCompositionAttribute, runs in a background thread after the page loads
  - friday/window.py: transparent=True, backdrop started on the "loaded" event
  - friday/ui/themes/win11.css; "win11" added to THEMES (label "Windows 11" in the settings panel)
  - Checked live on build 26200: blur shows wallpaper colours, STAYS when the window is inactive,
    drag / resize / buttons work, the other three themes look as before

- [x] Stage 23d: accent colour of the win11 theme follows Windows, 998 tests
  - friday/accent_logic.py (pure: palette parsing, accent and light picked from the palette, shades; 10 tests)
  - friday/accent_source.py (registry read, live-checked), friday/accent_publisher.py (polls every 3 s,
    publishes AccentChanged only when it changes; 6 tests), AccentChanged in ui_events.py / ui_bridge.py
  - window.fridayUi.setAccent writes a <style> rule limited to the win11 theme; the accent paints the
    user's message bubble, the idle circles and the border of the chosen settings option
  - Checked live: the colours follow a manual wallpaper change within about 3 s, the blur stays
  - The page fades the colours (1.2 s, about 30 fps) in app.js: fadeAccent; the CSS transition of the
    circles is switched off meanwhile (class accent-fading) so the circles and the bubble move together.
    Polling every 0.5 s. Checked live: from a wallpaper change to the start of the fade about 1-2 s
    (mostly Windows writing the registry late).

- [x] Stage 23e: veil over the abrupt blur redraw on wallpaper change, 1010 tests
  - friday/wallpaper_source.py (change time of TranscodedWallpaper), friday/wallpaper_watcher.py
    (polls 0.1 s, first write of a 2-4 write burst is the signal, 2 s minimum gap, errors survive)
  - UI event WallpaperChanging (ui_events.py, ui_bridge.py) -> window.fridayUi.wallpaperChanging()
  - app.js: a dark veil (#wallpaper-veil, win11 theme only) fades in over ~0.8 s, is lifted
    0.5 s after the new accent arrives, or by itself after 4 s if the accent does not change
  - Checked live: veil opacity 0.99 hides the blur snap completely (0.9 was not enough);
    the user is fine with the short dark pause

- [x] Stage 24a: window transparency per theme, storage and logic, 1041 tests
  - friday/transparency.py (percent 0..100 per theme, defaults: win11 40 = the old 60 % tint,
    the other themes 0; parse_percent, clean_percents, percent_for), settings_store keeps a
    "transparency" dict in data/settings.json, bad values are dropped, old files still load
  - Decisions (user): range 0-100 %; in classic / windows / black the slider makes the page
    background see-through over the acrylic base (clear glass there is postponed); in win11 it
    moves the Windows tint (tint = 100 - transparency)
  - Next: 24b service + WindowApi.set_transparency + event, 24c slider in the page,
    24d win11 tint through win_backdrop (the same value is not re-applied, may need a "kick")

- [x] Stage 24a-24d: window transparency per theme, 1077 tests
  - friday/transparency.py (percent 0..100 per theme; defaults: win11 40 = the old 60 % tint,
    other themes 0), settings_store keeps a "transparency" dict in data/settings.json (bad values
    dropped, old files still load), SettingsService.set_transparency (each theme keeps its own
    value; TransparencyChanged is sent after every theme change), WindowApi.set_transparency
  - Page: slider "Прозрачность" in the settings panel; app.js previews while dragging and saves
    on release; classic / windows / black: page background = --bg mixed with transparent
    (color-mix in styles.css), the acrylic base under it stays at the fixed 60 % tint
  - win11: friday/backdrop_logic.py opacity_for (tint = 100 - transparency), CHANGE_STEPS,
    friday/backdrop_tint.py (BackdropTint: events -> opacity), friday/win_backdrop.py is now the
    class Backdrop (start / set_opacity, changes the tint in a worker thread); window.py wires it
  - Checked live: 0 % opaque and 100 % clear glass in win11, per-theme values, slider value
    shown in the panel
  - Not checked: blur stays when the window is inactive after a tint change (if it goes flat,
    use KICK_STEPS instead of CHANGE_STEPS); restart keeps the value; the wallpaper veil is
    still #202020 (may look darker than the window at high transparency)
  - Postponed (user): clear glass in classic / windows / black (needs the acrylic tint to follow
    the slider there too)

- [x] Stage 24e: own tint colour per theme under the transparent page, 1075 tests
  - friday/backdrop_logic.py (TINT_COLORS, tint_for, opacity_for), friday/backdrop_tint.py,
    class Backdrop in friday/win_backdrop.py (set_tint), friday/window.py, styles.css
    (html, body background is transparent)
  - Found live: tint #000000 with opacity 0 makes Windows ignore the tint; black uses
    #010101, guarded by test_no_theme_gives_a_zero_gradient_value
  - Checked live: every theme changes with the slider
- [x] Stage 24f: wallpaper veil in every theme
  - app.js coverWallpaperChange without the win11 check; veil rules in styles.css, colour
    from --veil (classic #0c0f1d, black #010101, others #202020)
  - Checked live: the blur redraw is hidden in the classic and black themes

- [x] Stage 25a: tray icon, 1083 tests
  - friday/window_lifecycle.py (show / hide / quit, on_closing cancels the close until quit;
    tested), friday/tray.py (pystray, menu "Открыть" / "Выйти"; live-checked, no tests)
  - window.py binds the lifecycle and the closing event; voice.py starts the tray and
    closes it in finally; WindowControls.close now hides the window
  - requirements-local.txt: pystray, pillow
  - Checked live: icon in the tray, X and Alt+F4 hide the window, voice works while hidden,
    "Открыть" brings the window back with the blur and the theme intact, "Выйти" exits fully

- [x] Stage 25b-1/25b-2: the top-edge island as a standalone module, 1111 tests
  - friday/island_logic.py (pure: size 120x32, centred at the top with an 8 px margin, colour per
    state; 16 tests), friday/island.py (Island: its own thread owns the window, start / stop /
    set_state; set_state is safe from any thread through a queue, ignored when not running; a build
    failure gives start() == False; 12 tests with a fake view), friday/island_view.py (tkinter
    window, live-checked, no tests: frameless, always on top, transparent corners, never takes the
    focus, out of Alt+Tab), friday/island_probe.py (python -m friday.island_probe: cycles the states)
  - Checked live (standalone, not wired into the app): capsule at the top centre, stays above other
    windows, does not steal the focus, the dot changes colour per state.
  - Not wired yet: voice.py, window_lifecycle.py, UiEventBus. Open risk: tkinter in a background
    thread next to PyWebView (not checked together). Fallback: run the island as a separate process.
  - Next: 25b-3 wiring (island follows StateChanged), 25c (shown only while the window is hidden,
    hover, what it shows).

- [x] Stage 25b-3: the island is wired into the app, 1117 tests
  - friday/island_bridge.py (IslandBridge: subscribes to UiEventBus, forwards StateChanged to
    Island.set_state; a late subscriber gets the last state from the bus; close is safe without
    start; 6 tests)
  - voice.py: Island is started in main() after the tray; if it does not start, the app goes on
    without it (a warning in the log); the bridge and the island are closed in finally before the tray
  - Checked live: the island appears at the top centre, the window opens normally, the dot follows
    the states (loading / idle, listening, thinking, speaking), the island stays when the window is
    hidden to the tray, "Выйти" removes it and the process ends cleanly.
  - tkinter in its own thread works next to PyWebView (the risk noted in 25b-1/2 did not happen).
  - For now the island is shown ALWAYS while the app runs (variant A, chosen by the user).
  - Next: 25c (show only while the window is hidden, hover, what it shows).

- [x] Stage 25b-4: the island is a Qt window in its own process, 1117 tests
  - Reason: tkinter has no smooth edges and no soft glow (colour-key transparency only); the user
    wants room for many later ideas (hover, answer text, animations), so the island moved to Qt
    (PySide6) instead of patching tkinter. The main window stays on PyWebView (not touched).
  - friday/island_qt.py (the window, live-checked, no tests: frameless, always on top, never takes
    the focus, per-pixel transparency, smooth edges, soft glow, thin light border, state colour
    fades in 350 ms, the dot and the glow pulse while listening / speaking; commands arrive on
    stdin: "state <name>" / "quit"; prints "ready" when shown; exits when stdin closes, so a dead
    parent never leaves an orphan window)
  - friday/island_process.py (IslandProcess: starts `python -m friday.island_qt`, waits for
    "ready" up to 15 s, set_state writes a line, stop sends quit and kills a hanging process;
    same interface as the old Island: start / stop / set_state; 12 tests with a fake process)
  - voice.py: IslandProcess instead of Island; IslandBridge is unchanged. PySide6>=6.6 added to
    requirements-local.txt (CI stays light).
  - Removed: friday/island.py, island_view.py, island_probe.py, tests/test_island.py (the tkinter
    version). friday/island_logic.py stays: the Qt window takes the state colours from it.
  - Checked live: the island appears at the top centre with smooth edges and a glow, follows the
    states, stays when the window is hidden to the tray, disappears on "Выйти".
  - Next: 25c (show only while the window is hidden, hover, what it shows); the look of the island
    can still be tuned (size, glow, body colour).

- [x] Stage 25b-5: the island look and the themes, 1135 tests
  - Look: the island hangs from the top edge like a "notch" (straight part 150x34, concave
    shoulders of 10 px join it to the screen edge, bottom corners rounded 14 px), no glow, a
    plain dot of the state colour (it pulses lightly while listening / speaking). The dot is to be
    replaced by something else later (the user's wish). Clock / weather and the wavy bottom from
    the user's reference picture are NOT done (maybe later); the choice of the attachment style
    will move to the settings.
  - Themes: island_logic.py has STATE_COLORS_BY_THEME, BODY_COLORS (same as TINT_COLORS of the
    window), TEXT_COLORS, color_for(state, theme), body_for, text_color_for; the island process
    gets "theme <name>" through the stdin channel (IslandProcess.set_theme), IslandBridge forwards
    ThemeChanged (the bus replays the theme before the state to a late subscriber). Values are
    taken from the window's CSS: classic, windows, black, win11 (win11 idle dot is the fixed blue
    #3aa6d8, following the Windows accent is not done).
  - Checked live: all four themes, the colours follow the settings and survive a restart.
  - Next: 25b-6 the answer text in the island (two lines, font "Rubik", "Segoe UI", disappears
    1.5 s after she stops speaking, always visible island; the text option will go to the settings).

- [x] Stage 25b-6: the answer text in the island, 1153 tests
  - Channel: IslandProcess.show_text (base64 over stdin, never logged) / clear_text;
    island_logic.clip_text (collapses whitespace, keeps the END of a long text, 160 chars);
    IslandBridge forwards MessageAdded of the assistant, cancels the hide timer while she speaks
    (State.SPEAKING) and hides the text 1.5 s after the state leaves SPEAKING (also for replies
    that are not spoken); 18 new tests with fake island and fake timers.
  - Window (friday/island_qt.py, live-checked, no tests): the island expands in 0.35 s to 440 px,
    the dot moves left, the text sits on the right, up to two lines (the END of a longer text
    stays visible), font "Rubik" / "Segoe UI" 13 px, text colour from the theme, collapses back
    to the dot after clear.
  - Checked live: the user confirmed it works. Sizes (width 440, font 13, paddings, speed) are
    left as they are; the user stopped here because of message limits.
  - Next: replace the dot with something else (the user's wish); the text on/off option and the
    attachment style in the settings; win11 island following the Windows accent; remove the
    unused island_position / ISLAND_WIDTH from island_logic.py; clock / weather and the wavy
    bottom from the user's reference picture are only an idea.

- [x] Stage 25b-7: moving wavy bottom edge of the island, done
  - island_logic.py (WaveParams, WAVE_BY_STATE, wave_params, wave_offset, edge_gap, ease_params),
    island_qt.py (16 ms timer, WAVE_PAD, paintEvent draws the wavy edge and the light line).
  - The transparency bug is gone (checked live). The "level" channel (microphone loudness for the wave)
    is still a separate later stage.

- [x] Stage 26a: friday/text_reveal.py (pure logic: chunk_spans, reveal_end, progress_at, scroll_target, ease_toward)
- [x] Stage 26b: event SpeechChunkStarted (text and duration of each spoken chunk); ui_bridge ignores it silently
- [x] Stage 26c: the island reveals the answer text in step with her voice, 1238 tests
  - IslandProcess: reveal / chunk / done channels (reveal_chunk, finish_reveal); IslandBridge computes
    chunk spans and sends them; island_qt.py draws the revealed part (start_reveal, reveal_chunk, finish_reveal).
  - Unspoken replies and texts over 2500 chars are shown at once; a chunk not found in the text is ignored;
    when the state leaves SPEAKING the island gets "done" and shows the whole text, then hides it after 1.5 s.
  - Checked live: words go with the voice, the island height does not jump.

- [x] Stage 27a-27c: smoother island, 1249 tests
  - 27a: wave timer 6 ms (about 165 fps, monitor is 165 Hz) with Qt.PreciseTimer; wave easing is
    frame-rate independent (island_logic.blend_factor, WAVE_EASE_RATE).
  - 27b: island opening runs on the wave timer, not on QVariantAnimation (island_logic.smoothstep,
    step_toward; EXPAND_SECONDS 0.45); the window width is kept even.
  - 27c: fixed-size island window (never resized, the island is drawn inside it in paintEvent,
    WindowTransparentForInput, _place()), fps counter (env FRIDAY_ISLAND_FPS=1 writes
    "island fps: N" to data/island_fps.txt, one line per second).
  - Found with the counter: the colour and pulse animations called update() on their own, so in the
    listening state the window repainted 222-230 times a second. _on_color and _on_pulse no longer
    call update(); only the wave tick repaints.
  - Measured live in the running app (idle, listening, opening under the answer text): 166-167
    paintEvent calls a second, equal to the monitor rate.
  - KNOWN ISSUE (open, the user: "smoothness is strange", still looks like less than 60 fps): the
    counter counts paintEvent calls, not frames that reach the screen. Hypothesis, NOT verified: a
    Qt window with per-pixel transparency on Windows is presented through UpdateLayeredWindow (CPU
    path, not tied to the monitor refresh), so frames may be dropped or uneven. Only variant B can
    check it: draw through OpenGL or Qt Quick with vertical sync; a big change, transparency and
    edges would have to be re-checked (they broke once in 25b-7). Postponed by the user. Fixed in stage 28.
    - Still to do: 27e every word fades in (alpha by progress, no jump). Postponed together with the
    smoothness work below.

- [x] Stage 27d: the island follows the text, 1264 tests
  - Width: the body grows with the revealed text, from 150 px up to 440 px (island_logic.target_body_width,
    ease_width); the text is always wrapped at the widest layout width (WRAP_W), so lines do not jump.
  - Height: follows the visible lines, one line at first, two at most (island_logic.visible_lines_height);
    before this, a long answer opened the island to two lines at once.
  - Text scroll: when the text is longer than two lines it moves up smoothly (island_logic.scroll_for,
    SCROLL_EASE_RATE 10); WIDTH_EASE_RATE 14 is shared by width and height.
  - Tried and rolled back: the text drawn once into a QPixmap and moved by fractions of a pixel
    (hypothesis: Qt snaps text to whole pixels). No visible change, so it was removed.
  - KNOWN ISSUE (open, the user: "it always jitters", also in idle, and "the island looks not
    optimized"): the whole island window jitters, not only the text. This fits the layered-window
    hypothesis from stage 27 (UpdateLayeredWindow, CPU path, not tied to the monitor refresh), but it is
    still NOT verified. Ideas for later, the user decides: variant B (OpenGL or Qt Quick with vertical
    sync; transparency and edges must be re-checked) and lighter drawing (the window is fixed at the
    biggest size and repainted 166 times a second on the CPU; repaint only the changed area, or lower
    the tick when nothing moves, or a larger WAVE_STEP). Postponed by the user. Fixed in stage 28.

- [x] Stage 28: the island is a Qt Quick window, 1293 tests
  - Reason: the jitter of the island (KNOWN ISSUE in 27 / 27d) fits the layered-window hypothesis:
    a per-pixel transparent QWidget on Windows is presented through UpdateLayeredWindow (CPU path).
    The Qt Quick window draws through Direct3D11 with vertical sync, and the jitter is gone (checked
    live by the user, also under the answer text and in idle).
  - 28a: friday/island_model.py (IslandModel: wave, reveal, width, height, scroll, colour and pulse in
    one class without Qt; text is measured by a callable from outside), island_logic.ease_width with a
    minimum speed (the tail of the movement does not crawl); tests/test_island_ease.py, test_island_model.py.
  - 28b: friday/island_shape.py (body_outline and light_line as lists of points, pure geometry; tests/
    test_island_shape.py), friday/ui/island.qml (Shape + PathPolyline, FrameAnimation calls backend.frame),
    friday/island_quick.py (the window and the stdin reader, same protocol as the old island: state, theme,
    text, clear, reveal, chunk, done, quit; prints "ready"), tests/test_island_quick_assets.py (every
    backend.* name used by the QML exists in Python).
  - PySide6 6.12.0 has no font.families in QML: the font family is picked in Python (pick_family,
    backend.fontFamily).
  - 28c: IslandProcess starts friday.island_quick instead of friday.island_qt; island_bridge.py and the
    protocol are unchanged. Checked live in the running app: shape, colours, themes, text reveal with the
    voice, hide after 1.5 s, exit through the tray, all as with the old island, without the jitter.
  - 28d: friday/island_qt.py removed. The fps counter FRIDAY_ISLAND_FPS=1 still writes to
    data/island_fps.txt (now "island quick fps").
  - The probes island_web_probe.py, island_qtweb_probe.py, island_quick_probe.py are not committed.

- [x] Stage 27e: every word fades in on the island, 1318 tests
  - friday/word_fade.py (pure logic: spans (start, end, born), fade_alpha with a smooth start and end,
    FADE_SECONDS 0.25, live_spans, build_markup: escaped StyledText with <font color> for the words that
    are still fading); tests/test_word_fade.py (16), tests/test_island_fade.py (9).
  - IslandModel.markup: the new part of the text is added as a span when the reveal moves on (and when
    the reveal finishes, so the rest fades in too); the colour goes from the body colour to the text colour,
    because the island body is opaque. Text shown at once has no fade.
  - island_quick.py: property markup; island.qml: Text.StyledText with backend.markup.
  - Checked live: words fade in smoothly, 2-3 words with different brightness in the tail, line breaks did not
    change, no jitter, hide after 1.5 s as before.

- [x] Stage 29: looks of the island icon, chosen in the settings, 1390 tests
  - 29a: friday/island_looks.py (pure logic: look_shapes(look, state, t, pulse) gives rounded rectangles
    (cx, cy, w, h, radius) around the centre of the icon; looks: dot (the old circle, default), eyes (blink,
    wide open while listening, look up and sway while thinking, grow with the voice while speaking),
    equalizer (4 bars, still in idle, jumping while listening / speaking, a travelling wave while thinking);
    LOOKS, DEFAULT_LOOK, look_or_default). A new look = one function + its name in LOOKS + a label in app.js.
  - 29b: IslandModel.set_look / look / icon_shapes (icon time advances with the ticks, clamped like the
    rest); island_quick.py: properties iconCount (changes only with the look) and iconData (flat list of
    numbers, 5 per shape), stdin command "look <name>"; island.qml draws the shapes with a Repeater over
    iconCount, so the frame does not recreate elements.
  - 29c: IslandLookChanged event (remembered by the bus), settings key island_look (settings_store.CHOICES,
    SettingsService.set_island_look, snapshot "island_looks"), WindowApi.set_island_look, IslandProcess.set_look,
    IslandBridge forwards the event, a new section "Значок острова" in the settings panel (index.html, app.js).
    The choice is saved in data/settings.json and applies at once.
  - Checked live: all three looks, the choice survives a restart, the island keeps its smoothness.
  - Open: the user will invent a third look of his own and describe it; the size, speed and amplitude of the
    eyes and the equalizer are constants at the top of island_looks.py.
    

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
- UI Automation (`windows(visible_only=True)`) does not see a minimized window, so
  ym_ui._find_window() returns None for it. Minimized windows are found through Win32 by
  process id (window_restore.py). The line "expected one wave player, found 0" in the log
  can be a normal first poll before the page has drawn; it is not an error by itself.
- After My Wave starts, only a window that Friday itself restored is minimized back again.
- The wave link opens the wave page and brings the window to the front, but does not start playback
  (Play is still pressed by wave_ui). It does NOT switch the page of an already running app, so the link
  is used only when no Music process exists. Music goes to the tray only when closed while playing, and
  then the wave is already playing (ALREADY_PLAYING).
- Yandex Music gives its cover through SMTC as a 150x150 PNG (about 52 KB), also while paused. The cover is read only when the track (title + artist) changes. Animations of the circle are postponed by the user.
- Circles: the equalizer and dots are drawn at the right edge of the window (cx = width - 30). Loudness reaches them only in the LISTENING state; her own voice does not move them yet. The blobs look uses blur(48px) on big shapes: watch for lag on weaker machines.
- Known small issue (postponed by the user): the window jitters slightly when it appears at start. Idea for later: smooth fade-in or a start animation of the window.
- Themes: the idle colours of the circles come from --idle-1/2/3 of the theme; the other states set --c1/--c2/--c3 per state (per theme in themes/*.css). The same THEME / CIRCLES pair will move into an in-app settings screen later.
- Settings: only theme and circles look for now; new options go into CHOICES in settings_store.py, the service and the panel. The blobs look is very bright in the black theme (screen blending of a light grey): to be softened when the looks are tuned.
- Backdrop: Mica and Acrylic (DwmSetWindowAttribute) turn flat when the window is inactive and
  after a wallpaper or accent change; this is Windows behaviour, same as the Settings app. The old
  SetWindowCompositionAttribute acrylic (AccentState 4, tint 0x99202020) stays blurred when inactive,
  but only if the frame is "kicked": apply with the glass extended, then without, then with again
  (0.6 s between). Applying the same value twice does nothing. Extending the glass is NOT the problem.
- PyWebView paints the form with background_color; with transparent=True the form is painted black
  (win_backdrop._paint_form_black), because glass shows through pure black.
- The accent colour in the win11 theme is fixed (#4cc2ff). The registry AccentColor / AccentPalette
  follows the wallpaper slideshow; reading it every few seconds is the next step (23d).
- AccentPalette in the registry holds 8 shades from the lightest to the darkest (4 bytes each: R, G, B,
  unused). Index 1 is the accent, index 0 the light one (matches the Settings app in dark mode, checked
  on the user's wallpaper). The last shade is always #881798 and is not used.
- The accent publisher starts in voice.main(), not in the assistant thread, so the colour does not wait
  for the models to load. It works only under `python -m friday.voice` (not `python -m friday.window`).
- On a very light accent the idle circle is almost white. Fine for now; tune the shades if it bothers.
- Wallpaper change (23e): the wallpaper file is rewritten about 1.1 s BEFORE the accent changes in the
  registry and before the blur snaps (measured, same for manual and slideshow changes); the file
  event comes as a burst of 2-4 writes. Windows cannot be stopped from snapping the blur, so the page
  hides it under a veil. The veil must be nearly opaque (0.99): at 0.9 the snap was still visible.
- Transparency: the page is transparent in every theme; the slider changes the opacity of the
  theme's own tint colour (tint_for / opacity_for). A tint colour must never be pure black:
  with opacity 0 the whole GradientColor becomes 0 and Windows draws its own black.
  in the other themes it stays 60 % and the slider only thins the page background over it.
- Tray: the app now lives without a window; the only exit is the tray menu "Выйти". If the
  tray icon is not visible, it is under the hidden icons arrow of the taskbar.
- Island: Qt in a separate process (stdin protocol: "state <name>", "quit"). The window has no
  link to the app except the pipe. Blur under the island (like the win11 theme) is not done: Qt
  does not give it, it would need the same Windows calls as win_backdrop.py.
- Island fps counter: FRIDAY_ISLAND_FPS=1 writes to data/island_fps.txt (the island process has no
  visible console in the app: it starts with CREATE_NO_WINDOW). Standalone, `python -m friday.island_qt`
  also works. The file grows on every run: delete it when it is not needed.


## Next
Candidates (ask the user): FIRST: ask the user what is next. Island: third island look (the user's own idea), island settings (text on/off, attachment style), win11 accent for the island, settings for the island (text on/off, attachment style), win11 accent. ... Island: replace the dot, settings for the island (text on/off, attachment style), win11 accent, then 19b and the rest. Also decide what the minimize button does once the island exists. tune each circles look one by one (size, position, brightness, speed, reaction to the voice; the blobs in the black theme are too bright); Stage 19b: control by the music circle (click = pause / resume through MusicController, name and artist on hover); more options in the settings panel (wake word on / off, voice, and others); smooth appearance of the window (it jitters slightly at start); animations of the music circle, the island and the settings panel; circles reacting to her own voice while she speaks; wave by mood; a window or area screenshot instead of the whole screen; shorter spoken answers (screen descriptions and "tell me about ..." take 17-45 s to speak; the user left it as is for now). X2 push-to-talk stays in any case.