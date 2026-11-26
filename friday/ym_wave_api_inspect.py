"""Diagnostic probe: print signatures and docs of the new wave methods.

Usage:
    python -m friday.ym_wave_api_inspect

Read-only, nothing is sent to the server. Not part of the app.
"""

import inspect
import logging
import sys

log = logging.getLogger("ym_wave_api_inspect")

NAMES = (
    "rotor_wave_settings",
    "rotor_wave_last",
    "rotor_combined_session_landing",
    "rotor_combined_session_new",
    "rotor_session_new",
)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    from yandex_music import Client

    for name in NAMES:
        method = getattr(Client, name, None)
        if method is None:
            log.info("%s: not found", name)
            continue
        log.info("=== %s%s", name, inspect.signature(method))
        doc = inspect.getdoc(method) or "(no docstring)"
        log.info("%s", doc[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
