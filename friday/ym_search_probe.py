"""Probe: what does Yandex Music search return for a phrase?

    python -m friday.ym_search_probe "Полетели Киркоров"

Needs YM_TOKEN in .env. Prints the top results with the ids that are needed
to build a track link. The token is never printed.
Live-checked tool, no unit tests.
"""

from __future__ import annotations

import os
import sys

TOP = 5


def main(query: str) -> None:
    from dotenv import load_dotenv
    from yandex_music import Client

    load_dotenv()
    token = os.environ.get("YM_TOKEN", "").strip()
    if not token:
        print("YM_TOKEN is not set in .env")
        return
    try:
        client = Client(token).init()
        result = client.search(query, type_="track")
    except Exception as error:
        print(f"search failed: {type(error).__name__}: {error}")
        return
    tracks = result.tracks.results if result and result.tracks else []
    print(f"{len(tracks)} tracks found for {query!r}")
    for index, track in enumerate(tracks[:TOP], 1):
        artists = ", ".join(artist.name or "?" for artist in track.artists)
        album_id = track.albums[0].id if track.albums else None
        print(
            f"#{index} {artists} - {track.title!r} version={track.version!r} "
            f"available={track.available}"
        )
        print(f"    https://music.yandex.ru/album/{album_id}/track/{track.id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: python -m friday.ym_search_probe "<phrase>"')
    else:
        main(sys.argv[1])
