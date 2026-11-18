# Friday 2.0

An open-source, test-driven voice assistant for Windows, written in Python.

**Status:** early development (stages 0-9 done). It already works as a voice
chat that can also control Yandex Music: hold the mouse side button X2, speak,
hear the answer. Not a finished product yet.

## Goals

- Fast and reliable: every module is covered by tests.
- Free to run: cloud LLM via a chain of free providers.
- Features: voice control, Yandex Music control, screen vision, long-term memory.

## Current features

- Push-to-talk on the mouse side button X2
- Speech recognition on the GPU (faster-whisper)
- Cloud LLM with a fallback chain of free providers
- Spoken answers (Edge TTS)
- Short dialogue memory
- Desktop window (PyWebView) with the chat and a state indicator
- Yandex Music control by voice (pause, play, next, previous, what's playing)
- Play a song or a whole artist in Yandex Music by name (needs `YM_TOKEN` in `.env`)
- Start My Wave in Yandex Music by voice: "включи мою волну" (the My Wave page must be open in the app)
- Long-term memory by voice: "запомни, что ...", "что ты обо мне помнишь", "забудь про ..."

## Privacy

Saved facts live only in `data/memory/facts.json` on your machine (git-ignored). They are
sent to the cloud LLM providers as part of the prompt on every turn, so do not tell the
assistant anything you do not want to share with them.

## Development

    py -3.11 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements-local.txt
    pytest

## Running

Copy `.env.example` to `.env` and fill it in, then:

    python -m friday.voice

Hold the mouse side button X2 and speak. Close the window to exit.
Speech recognition needs an NVIDIA GPU (tested on an RTX 5050).

Русская версия: [README.ru.md](README.ru.md). License: MIT.

Unofficial fan project. Not affiliated with Marvel or Disney.