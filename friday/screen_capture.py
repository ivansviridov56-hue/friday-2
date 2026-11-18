"""Screen capture for the vision feature: grab, downscale, encode as JPEG.

What to capture is decided by the `grab` function (full screen for now; a
rectangle or a window can be added later as another grabber). The screenshot
only lives in memory and goes to the cloud vision provider: the caller decides
when to take it.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

log = logging.getLogger(__name__)

DEFAULT_MAX_WIDTH = 1536
DEFAULT_QUALITY = 85
MIME = "image/jpeg"

Grabber = Callable[[], Image.Image]


class ScreenCaptureError(Exception):
    """The screen could not be captured."""


@dataclass(frozen=True)
class Screenshot:
    data: bytes
    mime: str
    width: int
    height: int
    source_width: int
    source_height: int


def fit_size(width: int, height: int, max_width: int) -> tuple[int, int]:
    """Scale down to max_width keeping the aspect ratio; never scale up."""
    if width <= max_width:
        return width, height
    return max_width, max(1, round(height * max_width / width))


def _check(max_width: int, quality: int) -> None:
    if max_width < 1:
        raise ValueError("max_width must be at least 1")
    if not 1 <= quality <= 95:
        raise ValueError("quality must be between 1 and 95")


def encode(image: Image.Image, max_width: int, quality: int) -> Screenshot:
    """Downscale (never upscale) and encode as JPEG."""
    _check(max_width, quality)
    rgb = image.convert("RGB")
    source_width, source_height = rgb.size
    size = fit_size(source_width, source_height, max_width)
    if size != rgb.size:
        rgb = rgb.resize(size, Image.Resampling.LANCZOS)
    buffer = BytesIO()
    rgb.save(buffer, "JPEG", quality=quality)
    return Screenshot(
        buffer.getvalue(), MIME, rgb.width, rgb.height, source_width, source_height
    )


def grab_full_screen() -> Image.Image:
    """Screenshot of the primary screen in real pixels (Windows)."""
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass  # already set by the window toolkit, or not Windows
    from PIL import ImageGrab

    return ImageGrab.grab()


def capture_screen(
    grab: Grabber = grab_full_screen,
    max_width: int = DEFAULT_MAX_WIDTH,
    quality: int = DEFAULT_QUALITY,
) -> Screenshot:
    _check(max_width, quality)
    try:
        image = grab()
    except Exception as exc:
        log.exception("screen capture failed")
        raise ScreenCaptureError(type(exc).__name__) from exc
    shot = encode(image, max_width, quality)
    log.info(
        "screenshot %dx%d -> %dx%d, %d KB",
        shot.source_width,
        shot.source_height,
        shot.width,
        shot.height,
        len(shot.data) // 1024,
    )
    return shot


def main() -> None:
    """Live check: take a screenshot and save it to a temp file to look at."""
    import tempfile
    import time
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    started = time.perf_counter()
    shot = capture_screen()
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    path = Path(tempfile.gettempdir()) / "friday_screen_check.jpg"
    path.write_bytes(shot.data)
    print(f"{shot.width}x{shot.height}, {len(shot.data) // 1024} KB, {elapsed_ms} ms")
    print(path)


if __name__ == "__main__":
    main()
