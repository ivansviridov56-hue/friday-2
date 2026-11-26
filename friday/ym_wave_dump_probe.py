"""Diagnostic probe: dump the new-style wave settings and the last wave.

Usage:
    python -m friday.ym_wave_dump_probe

Read-only. The token is never printed. Not part of the app.
"""

import json
import logging
import os
import sys

log = logging.getLogger("ym_wave_dump_probe")


def _token() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        log.info("python-dotenv is not installed, using the process environment only")
    return os.environ.get("YM_TOKEN", "")


def _dump(title: str, obj: object) -> None:
    log.info("=== %s", title)
    if obj is None:
        log.info("None")
        return
    to_dict = getattr(obj, "to_dict", None)
    data = to_dict() if callable(to_dict) else repr(obj)
    text = json.dumps(data, ensure_ascii=False, indent=1, default=str)
    log.info("%s", text[:6000])


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    token = _token()
    if not token:
        log.error("YM_TOKEN is empty")
        return 1
    from yandex_music import Client

    client = Client(token).init()
    _dump(
        "rotor_wave_settings(user:onyourwave)",
        client.rotor_wave_settings("user:onyourwave"),
    )
    _dump("rotor_wave_last()", client.rotor_wave_last())
    return 0


if __name__ == "__main__":
    sys.exit(main())
