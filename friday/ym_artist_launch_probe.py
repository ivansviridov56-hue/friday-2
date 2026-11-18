"""Live check of stage 7e: search an artist, start it, report the status.

    python -m friday.ym_artist_launch_probe "Киркорова"

Needs YM_TOKEN in .env. The token is never printed.
"""

from __future__ import annotations

import logging
import os
import sys

from friday.artist_search import ArtistSearch


def main(phrase: str) -> None:
    from dotenv import load_dotenv

    from friday.ym_artist_ui import build_artist_launcher

    load_dotenv()
    found = ArtistSearch(os.environ.get("YM_TOKEN")).find(phrase)
    print("search:", found.status.value)
    if found.artist is None:
        return
    print("artist:", found.artist.name)
    result = build_artist_launcher().launch(found.artist.link, found.artist.name)
    print("launch:", result.status.value, "| page name:", repr(result.found_title))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print('usage: python -m friday.ym_artist_launch_probe "<artist>"')
    else:
        main(sys.argv[1])
