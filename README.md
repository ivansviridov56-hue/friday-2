# Friday 2.0

An open-source, test-driven voice assistant for Windows, written in Python.

**Status:** early development (stages 0-31 done). It already works as a voice
chat with a desktop window: hold the mouse side button X2 (or say "Пятница"),
speak, hear the answer. It can also control Yandex Music, remember facts and
describe the screen. Not a finished product yet.

## Goals

- Fast and reliable: every module is covered by tests.
- Free to run: cloud LLM via a chain of free providers.
- Features: voice control, Yandex Music control, screen vision, long-term memory.

## Current features

- Push-to-talk on the mouse side button X2
- Wake word (optional): say "Пятница, ..." instead of holding X2 (`WAKE_WORD=1` in `.env`, off by default)
- Text input in the window: a typed phrase works like a spoken one, commands included
- Speech recognition on the GPU (faster-whisper)
- Cloud LLM with a fallback chain of free providers
- Spoken answers: local Silero voice by default, Edge TTS as an option (`TTS_ENGINE=edge` in `.env`)
- Short dialogue memory
- Long-term memory by voice: "запомни, что ...", "что ты обо мне помнишь", "забудь про ..."
- Yandex Music control by voice (pause, play, next, previous, what's playing)
- Play a song or a whole artist in Yandex Music by name (needs `YM_TOKEN` in `.env`)
- Start My Wave in Yandex Music by voice: "включи мою волну" (works when the app is closed or minimized; if it is open on another page, open My Wave first)
- My Wave by mood: "включи мою спокойную волну" (active, fun, calm, sad)
- Describe the screen by voice: "что на экране" (the screenshot is sent to a cloud vision model)
- Frameless desktop window (PyWebView) with the chat, a state indicator and the cover of the current Yandex Music track
- Colour themes: classic, windows, black and win11 (a real blurred window background, the accent follows Windows)
- Window transparency slider, kept separately for each theme
- Switchable look of the background circles (classic, blobs, equalizer, dots)
- Settings panel (gear in the header): theme, transparency, circles look and island icon, saved between runs (`THEME` and `CIRCLES` in `.env` are only the starting values)
- Tray icon: closing the window hides it to the tray, voice keeps working; exit through the tray menu
- Island at the top edge of the screen: shows her state and reveals the answer word by word in step with her voice; four icon looks (dot, eyes, equalizer, blobs)

## Privacy

Saved facts live only in `data/memory/facts.json` on your machine (git-ignored). They are
sent to the cloud LLM providers as part of the prompt on every turn, so do not tell the
assistant anything you do not want to share with them.
When you ask what is on the screen, a screenshot of your whole screen is taken, downscaled and sent
to a cloud vision model (Cloudflare Workers AI, with OpenRouter as a fallback). It is kept in memory
only and is never saved to disk, but close anything private before asking.
If you turn the wake word on, the microphone is listened to continuously and everything said near
it is recognized on your machine by the local Whisper model. Audio is never saved, and recognized
text is not logged unless `WAKE_DEBUG=1` (it prints what was heard to the console, for tuning only).
Phrases that do not start with the name are dropped on your machine; the text of a phrase that does
is sent to the cloud LLM providers like any other command.
The default voice is the Silero TTS model `v5_ru`, which runs locally on the CPU. It is downloaded
on the first start by the `silero` package and is not part of this repository. The Silero models are
published under a non-commercial licence (CC BY-NC, see https://github.com/snakers4/silero-models),
so they are fine for personal use but not for commercial use. For a commercial setup, use
`TTS_ENGINE=edge` or another voice.

## Development

    py -3.11 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements-local.txt
    pytest

## Running

Copy `.env.example` to `.env` and fill it in, then:

    python -m friday.voice

Hold the mouse side button X2 and speak, or type in the window. Closing the
window only hides it to the tray; to exit, choose "Выйти" in the tray icon menu.
Speech recognition needs an NVIDIA GPU (tested on an RTX 5050).

Русская версия: [README.ru.md](README.ru.md). License: MIT.

Unofficial fan project. Not affiliated with Marvel or Disney.