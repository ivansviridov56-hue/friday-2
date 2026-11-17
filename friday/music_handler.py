"""Glue: phrase -> music command -> MusicController call -> answer.

Short success confirmations are shown in the window but not spoken, so quick
repeated commands ("next", "next") are not lost while the assistant is talking.
Errors and "what is playing" are always spoken.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from friday.assistant import CommandReply
from friday.music import PAUSED, RESUMED, SKIPPED, WENT_BACK
from friday.music_commands import MusicCommand, parse_music_command

_QUIET_ANSWERS = frozenset({PAUSED, RESUMED, SKIPPED, WENT_BACK})


class MusicActions(Protocol):
    def play(self) -> str: ...
    def pause(self) -> str: ...
    def skip_next(self) -> str: ...
    def skip_previous(self) -> str: ...
    def now_playing(self) -> str: ...


def make_music_handler(
    music: MusicActions,
) -> Callable[[str], CommandReply | None]:
    """Return a handler: the reply for a music command, None for other speech."""
    actions = {
        MusicCommand.PAUSE: music.pause,
        MusicCommand.PLAY: music.play,
        MusicCommand.NEXT: music.skip_next,
        MusicCommand.PREVIOUS: music.skip_previous,
        MusicCommand.NOW_PLAYING: music.now_playing,
    }

    def handle(text: str) -> CommandReply | None:
        command = parse_music_command(text)
        if command is None:
            return None
        answer = actions[command]()
        return CommandReply(answer, spoken=answer not in _QUIET_ANSWERS)

    return handle
