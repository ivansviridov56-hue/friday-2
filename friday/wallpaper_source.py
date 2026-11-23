"""Reads the change time of the Windows wallpaper file."""

from __future__ import annotations

import os
from pathlib import Path


def wallpaper_path() -> Path | None:
    """The file Windows rewrites on every wallpaper change, None if APPDATA is unknown."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return Path(appdata) / "Microsoft" / "Windows" / "Themes" / "TranscodedWallpaper"


class FileWallpaperSource:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else wallpaper_path()

    def stamp(self) -> int | None:
        """Last change time of the file in nanoseconds, None if it cannot be read."""
        if self._path is None:
            return None
        try:
            return self._path.stat().st_mtime_ns
        except OSError:
            return None
