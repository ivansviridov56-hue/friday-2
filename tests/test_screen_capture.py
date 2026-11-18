from io import BytesIO

import pytest
from PIL import Image

from friday.screen_capture import (
    ScreenCaptureError,
    capture_screen,
    encode,
    fit_size,
)


@pytest.mark.parametrize(
    ("size", "max_width", "expected"),
    [
        ((3000, 1500), 1500, (1500, 750)),
        ((800, 600), 1500, (800, 600)),
        ((3000, 1), 1000, (1000, 1)),
    ],
)
def test_fit_size(size, max_width, expected) -> None:
    assert fit_size(size[0], size[1], max_width) == expected


def test_encode_downscales_keeping_ratio() -> None:
    shot = encode(Image.new("RGB", (3000, 1500), "white"), max_width=1500, quality=85)
    assert (shot.width, shot.height) == (1500, 750)
    assert (shot.source_width, shot.source_height) == (3000, 1500)
    assert Image.open(BytesIO(shot.data)).size == (1500, 750)


def test_encode_does_not_upscale() -> None:
    shot = encode(Image.new("RGB", (800, 600), "white"), max_width=1500, quality=85)
    assert (shot.width, shot.height) == (800, 600)


def test_encode_handles_rgba() -> None:
    shot = encode(Image.new("RGBA", (100, 100), (255, 0, 0, 128)), 1500, 85)
    assert (shot.width, shot.height) == (100, 100)


def test_encode_returns_jpeg() -> None:
    shot = encode(Image.new("RGB", (100, 100), "red"), 1500, 85)
    assert shot.mime == "image/jpeg"
    assert shot.data.startswith(b"\xff\xd8")


def test_encode_rejects_bad_settings() -> None:
    image = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        encode(image, max_width=0, quality=85)
    with pytest.raises(ValueError):
        encode(image, max_width=1500, quality=0)
    with pytest.raises(ValueError):
        encode(image, max_width=1500, quality=96)


def test_capture_screen_uses_grabber_and_default_width() -> None:
    image = Image.new("RGB", (2000, 1000), "white")
    shot = capture_screen(grab=lambda: image)
    assert (shot.width, shot.height) == (1536, 768)


def test_capture_screen_passes_settings() -> None:
    image = Image.new("RGB", (2000, 1000), "white")
    shot = capture_screen(grab=lambda: image, max_width=500, quality=50)
    assert (shot.width, shot.height) == (500, 250)


def test_capture_screen_wraps_grabber_errors() -> None:
    def broken() -> Image.Image:
        raise OSError("no display")

    with pytest.raises(ScreenCaptureError):
        capture_screen(grab=broken)


def test_capture_screen_checks_settings_before_grabbing() -> None:
    calls: list[int] = []

    def grab() -> Image.Image:
        calls.append(1)
        return Image.new("RGB", (10, 10))

    with pytest.raises(ValueError):
        capture_screen(grab=grab, max_width=0)
    assert calls == []
