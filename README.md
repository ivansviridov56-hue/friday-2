# Friday 2.0

An open-source, test-driven voice assistant for Windows, written in Python.

**Status:** early development (stages 0-5 done). It already works as a voice
chat: hold the mouse side button X2, speak, hear the answer. Not a finished
product yet.

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