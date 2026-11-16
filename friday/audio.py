"""Audio playback."""

from __future__ import annotations

import io
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


class PygamePlayer:
    """Play mp3 bytes and block until they finish."""

    def __init__(self) -> None:
        import pygame

        self._pygame = pygame
        pygame.mixer.init()

    def play(self, audio: bytes) -> None:
        music = self._pygame.mixer.music
        music.load(io.BytesIO(audio), "mp3")
        music.play()
        while music.get_busy():
            self._pygame.time.wait(20)
