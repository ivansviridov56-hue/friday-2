"""Live check of stage 7c: search a phrase, start the track, report the status.

    python -m friday.ym_launch_probe "Полетели Киркоров"

Needs YM_TOKEN in .env. The token is never printed.
"""

from __future__ import annotations

import logging
import os
import sys

from friday.music_search import SearchStatus, TrackSearch


def main(phrase: str) -> None:
    from dotenv import load_dotenv

    from friday.ym_ui import build_launcher

    load_dotenv()
    found = TrackSearch(os.environ.get("YM_TOKEN")).find(phrase)
    print("search:", found.status.value)
    if found.status is not SearchStatus.FOUND or found.track is None:
        return
    track = found.track
    print("track: ", track.display_name)
    result = build_launcher().launch(track.link, track.title)
    print("launch:", result.status.value, "| panel title:", repr(result.found_title))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print('usage: python -m friday.ym_launch_probe "<phrase>"')
    else:
        main(sys.argv[1])
