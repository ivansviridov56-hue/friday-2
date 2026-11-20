"""Audio playback."""

from __future__ import annotations

import io
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def audio_kind(audio: bytes) -> str:
    """Edge gives mp3, the local Windows voice gives WAV (it starts with RIFF)."""
    return "wav" if audio[:4] == b"RIFF" else "mp3"


class PygamePlayer:
    """Play mp3 or WAV bytes and block until they finish."""

    def __init__(self) -> None:
        import pygame

        self._pygame = pygame
        pygame.mixer.init()

    def play(self, audio: bytes) -> None:
        music = self._pygame.mixer.music
        music.load(io.BytesIO(audio), audio_kind(audio))
        music.play()
        while music.get_busy():
            self._pygame.time.wait(20)
