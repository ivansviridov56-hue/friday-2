import pytest

from friday.backdrop_logic import (
    KICK_STEPS,
    MIN_BUILD,
    backdrop_supported,
    enable_backdrop,
    hex_to_rgb,
    make_tint,
    parse_accent,
    run_steps,
)


def test_parse_accent_swaps_channels():
    assert parse_accent(0xFF49362C) == "#2c3649"


def test_parse_accent_rejects_out_of_range():
    with pytest.raises(ValueError):
        parse_accent(-1)
    with pytest.raises(ValueError):
        parse_accent(0x1FFFFFFFF)


def test_hex_to_rgb():
    assert hex_to_rgb("#112233") == (0x11, 0x22, 0x33)


@pytest.mark.parametrize("bad", ["112233", "#123", "#12345g7", ""])
def test_hex_to_rgb_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        hex_to_rgb(bad)


def test_make_tint_default_matches_probe_value():
    assert make_tint() == 0x99202020


def test_make_tint_channel_order():
    assert make_tint("#112233", 1.0) == 0xFF332211


def test_make_tint_clamps_opacity():
    assert make_tint("#000000", 5.0) == 0xFF000000
    assert make_tint("#000000", -1.0) == 0x00000000


def test_backdrop_supported_by_build():
    assert backdrop_supported(26200)
    assert backdrop_supported(MIN_BUILD)
    assert not backdrop_supported(MIN_BUILD - 1)


def test_kick_steps_change_and_restore_the_frame():
    assert [s.extend for s in KICK_STEPS] == [True, False, True]


def test_run_steps_calls_in_order_and_sleeps():
    calls, sleeps = [], []

    def apply(extend):
        calls.append(extend)
        return True

    assert run_steps(apply, sleep=sleeps.append) is True
    assert calls == [True, False, True]
    assert sleeps == [0.6]


def test_run_steps_stops_on_failure():
    calls = []

    def apply(extend):
        calls.append(extend)
        return False

    assert run_steps(apply, sleep=lambda _: None) is False
    assert calls == [True]


def test_run_steps_survives_exception():
    def apply(extend):
        raise OSError("boom")

    assert run_steps(apply, sleep=lambda _: None) is False


def test_enable_backdrop_skips_old_windows():
    calls = []
    assert (
        enable_backdrop(
            lambda extend: calls.append(extend) or True, MIN_BUILD - 1, lambda _: None
        )
        is False
    )
    assert calls == []


def test_enable_backdrop_on_supported_build():
    assert enable_backdrop(lambda extend: True, 26200, lambda _: None) is True
