from __future__ import annotations

import pytest
from PIL import Image

from friday.tray_icon import PALETTES, make_tray_icon, normalize_state, palette_for


def _brightness(rgba: tuple[int, int, int, int]) -> int:
    return rgba[0] + rgba[1] + rgba[2]


def _pixel(image: Image.Image, xy: tuple[int, int]) -> tuple[int, int, int, int]:
    pixel = image.getpixel(xy)
    assert isinstance(pixel, tuple) and len(pixel) == 4
    return (int(pixel[0]), int(pixel[1]), int(pixel[2]), int(pixel[3]))


def test_default_icon_is_rgba_64() -> None:
    image = make_tray_icon()
    assert isinstance(image, Image.Image)
    assert image.mode == "RGBA"
    assert image.size == (64, 64)


@pytest.mark.parametrize("size", [16, 32, 64, 128])
def test_custom_sizes(size: int) -> None:
    image = make_tray_icon(size=size)
    assert image.mode == "RGBA"
    assert image.size == (size, size)


@pytest.mark.parametrize("bad_size", [0, -1, 15, 513, True])
def test_invalid_size_raises(bad_size: int | bool) -> None:
    with pytest.raises(ValueError):
        make_tray_icon(size=bad_size)


def test_corners_are_transparent() -> None:
    image = make_tray_icon(size=64)
    for point in [(0, 0), (63, 0), (0, 63), (63, 63)]:
        assert _pixel(image, point)[3] == 0


def test_three_voice_bars_are_bright_and_separated() -> None:
    image = make_tray_icon(size=64)
    bars = [_pixel(image, (x, 32)) for x in (21, 32, 43)]
    gaps = [_pixel(image, (x, 32)) for x in (26, 37)]

    for bar in bars:
        assert bar[3] >= 250
        assert min(bar[:3]) >= 220

    for gap in gaps:
        assert gap[3] >= 250
        assert min(gap[:3]) <= 150
        assert _brightness(gap) < _brightness(bars[1]) - 150


def test_states_produce_distinct_icons() -> None:
    states = ("idle", "listening", "thinking", "speaking", "error")
    rendered = {state: make_tray_icon(state=state).tobytes() for state in states}
    assert len(set(rendered.values())) == len(states)


def test_unknown_state_falls_back_to_idle() -> None:
    assert (
        make_tray_icon(state="unknown").tobytes()
        == make_tray_icon(state="idle").tobytes()
    )


def test_state_name_is_trimmed_and_case_insensitive() -> None:
    assert (
        make_tray_icon(state="  LISTENING ").tobytes()
        == make_tray_icon(state="listening").tobytes()
    )


def test_accent_changes_idle_icon_only() -> None:
    idle_default = make_tray_icon(state="idle").tobytes()
    idle_accent = make_tray_icon(state="idle", accent="#ff8800").tobytes()
    assert idle_accent != idle_default

    listening_default = make_tray_icon(state="listening").tobytes()
    listening_accent = make_tray_icon(state="listening", accent="#ff8800").tobytes()
    assert listening_accent == listening_default


@pytest.mark.parametrize("bad_accent", [None, "", "red", "#12345", "#gggggg", "4cc2ff"])
def test_invalid_accent_is_ignored(bad_accent: str | None) -> None:
    expected = make_tray_icon(state="idle").tobytes()
    assert make_tray_icon(state="idle", accent=bad_accent).tobytes() == expected


def test_public_helpers() -> None:
    assert normalize_state(" Speaking ") == "speaking"
    assert normalize_state(None) == "idle"
    assert palette_for("error") == PALETTES["error"]
