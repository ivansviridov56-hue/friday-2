import pytest

from friday.accent_logic import (
    accent_vars,
    parse_palette,
    pick_accent,
    rgb_triplet,
    shade,
)


def test_parse_palette_reads_rgb_and_skips_the_unused_byte():
    data = bytes([0x99, 0xEB, 0xFF, 0x00, 0x4C, 0xC2, 0xFF, 0x00])
    assert parse_palette(data) == ["#99ebff", "#4cc2ff"]


@pytest.mark.parametrize("bad", [b"", b"\x00" * 4, b"\x00" * 9])
def test_parse_palette_rejects_odd_sizes(bad):
    with pytest.raises(ValueError):
        parse_palette(bad)


def test_pick_accent_returns_accent_and_light():
    assert pick_accent(["#99ebff", "#4cc2ff", "#0091f8"]) == ("#4cc2ff", "#99ebff")


def test_pick_accent_rejects_short_palette():
    with pytest.raises(ValueError):
        pick_accent(["#99ebff"])


def test_shade_keeps_and_darkens():
    assert shade("#102040", 1.0) == "#102040"
    assert shade("#102040", 0.5) == "#081020"
    assert shade("#102040", 0.0) == "#000000"


def test_shade_clamps_factor():
    assert shade("#102040", 3.0) == "#102040"
    assert shade("#102040", -1.0) == "#000000"


def test_rgb_triplet():
    assert rgb_triplet("#4cc2ff") == "76, 194, 255"


def test_accent_vars():
    result = accent_vars("#4cc2ff", "#99ebff")
    assert result["--accent"] == "#4cc2ff"
    assert result["--accent-light"] == "#99ebff"
    assert result["--accent-rgb"] == "76, 194, 255"
    assert result["--idle-1"] == "#3d9bcc"
    assert result["--idle-2"] == "#2a6b8c"
    assert set(result) >= {"--idle-3"}
