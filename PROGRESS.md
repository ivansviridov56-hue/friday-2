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


## Next
Stage 14 candidates (ask the user): window: left logo strip, frameless window with its own buttons,
circles reacting to her own voice while she speaks, wave by mood, a window or area screenshot instead of the whole
screen, shorter spoken answers (screen descriptions and "tell me about ..." take 17-45 s to speak;
the user left it as is for now). X2 push-to-talk stays in any case.