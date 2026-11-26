"""Diagnostic probe: read (and optionally set) My Wave mood settings via the API.

Usage:
    python -m friday.ym_wave_settings_probe            # read only
    python -m friday.ym_wave_settings_probe --set calm # fun | active | calm | sad | all

Not part of the app. The token is never printed.
"""

import argparse
import logging
import os
import sys

log = logging.getLogger("ym_wave_settings_probe")

STATION = "user:onyourwave"
MOODS = ("fun", "active", "calm", "sad", "all")


def _load_token() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        log.info("python-dotenv is not installed, using the process environment only")
    return os.environ.get("YM_TOKEN", "")


def _describe(settings: object) -> str:
    fields = ("mood_energy", "diversity", "language", "mood", "energy")
    return ", ".join(f"{name}={getattr(settings, name, '?')}" for name in fields)


def _read(client: object) -> None:
    rotor_methods = [name for name in dir(client) if "rotor" in name]
    log.info("rotor methods in the library: %s", rotor_methods)
    results = client.rotor_station_info(STATION)  # type: ignore[attr-defined]
    log.info("rotor_station_info returned %d item(s)", len(results))
    for index, result in enumerate(results):
        for attr in ("settings", "settings2"):
            settings = getattr(result, attr, None)
            if settings is None:
                log.info("[%d] %s: none", index, attr)
            else:
                log.info("[%d] %s: %s", index, attr, _describe(settings))


def _set(client: object, mood: str) -> None:
    results = client.rotor_station_info(STATION)  # type: ignore[attr-defined]
    current = results[0].settings2 if results else None
    diversity = getattr(current, "diversity", None) or "default"
    language = getattr(current, "language", None) or "any"
    log.info(
        "keeping diversity=%s language=%s, setting mood_energy=%s",
        diversity,
        language,
        mood,
    )
    ok = client.rotor_station_settings2(  # type: ignore[attr-defined]
        STATION, mood_energy=mood, diversity=diversity, language=language
    )
    log.info("rotor_station_settings2 returned: %r", ok)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=MOODS, default=None)
    args = parser.parse_args()

    token = _load_token()
    if not token:
        log.error("YM_TOKEN is empty")
        return 1
    from yandex_music import Client

    client = Client(token).init()
    _read(client)
    if args.set:
        _set(client, args.set)
        log.info("--- after the change ---")
        _read(client)
    return 0


if __name__ == "__main__":
    sys.exit(main())
