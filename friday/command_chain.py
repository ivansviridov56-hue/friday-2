"""Build the voice command chain in one place, in a fixed order.

voice.py once lost the My Wave handler and no test noticed. Now the chain
is built by name: a missing or unknown handler is an error at startup.
"""

from __future__ import annotations

from collections.abc import Mapping

from friday.play_handler import Handler, chain_handlers

# Earlier handlers win when two of them could answer the same phrase.
COMMAND_ORDER = (
    "memory",
    "screen",
    "wave_mood",
    "wave",
    "play",
    "artist",
    "music",
)


def build_command_chain(handlers: Mapping[str, Handler]) -> Handler:
    missing = [name for name in COMMAND_ORDER if name not in handlers]
    unknown = [name for name in handlers if name not in COMMAND_ORDER]
    if missing or unknown:
        raise ValueError(
            f"command chain mismatch: missing={missing}, unknown={unknown}"
        )
    return chain_handlers(*(handlers[name] for name in COMMAND_ORDER))
