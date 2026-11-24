import pytest

from friday.text_reveal import (
    chunk_spans,
    ease_toward,
    progress_at,
    reveal_end,
    scroll_target,
)

TEXT = "Hello there. How are you doing today?"
CHUNKS = ["Hello there.", "How are you doing today?"]


def test_chunk_spans_find_chunks_in_order():
    assert chunk_spans(TEXT, CHUNKS) == [(0, 12), (13, 37)]


def test_chunk_spans_repeated_chunk_uses_next_occurrence():
    assert chunk_spans("Yes. Yes.", ["Yes.", "Yes."]) == [(0, 4), (5, 9)]


def test_chunk_spans_missing_chunk_takes_next_stretch():
    assert chunk_spans("abc def", ["zzz"]) == [(0, 3)]


def test_chunk_spans_no_chunks():
    assert chunk_spans(TEXT, []) == []


def test_progress_at_is_clamped():
    assert progress_at(1, 2) == 0.5
    assert progress_at(3, 2) == 1.0
    assert progress_at(-1, 2) == 0.0


def test_progress_at_zero_duration_is_done():
    assert progress_at(0.5, 0) == 1.0


def test_reveal_start_and_end():
    assert reveal_end(TEXT, 13, 37, 0) == 13
    assert reveal_end(TEXT, 13, 37, 1) == 37
    assert reveal_end(TEXT, 13, 37, -0.5) == 13
    assert reveal_end(TEXT, 13, 37, 1.5) == 37


def test_reveal_shows_the_word_the_speech_has_reached():
    assert reveal_end(TEXT, 13, 37, 0.01) == 16  # "How"
    assert reveal_end(TEXT, 13, 37, 0.5) == 30  # "... doing"


def test_reveal_stops_before_a_space():
    assert reveal_end(TEXT, 13, 37, 0.46) == 24  # the index falls on a space


def test_reveal_never_cuts_a_word_and_never_goes_back():
    last = 13
    for i in range(0, 101):
        shown = reveal_end(TEXT, 13, 37, i / 100)
        assert shown >= last
        assert shown <= 37
        assert shown in (13, 37) or TEXT[shown] == " "
        last = shown


def test_reveal_empty_chunk_shows_nothing_new():
    assert reveal_end(TEXT, 5, 5, 0.5) == 5


def test_reveal_clamps_out_of_range_span():
    assert reveal_end("abc", 5, 9, 0.5) == 3


def test_scroll_target_keeps_last_lines_visible():
    assert scroll_target(1, 2) == 0
    assert scroll_target(2, 2) == 0
    assert scroll_target(3, 2) == 1
    assert scroll_target(5, 2) == 3


def test_scroll_target_rejects_bad_max_lines():
    with pytest.raises(ValueError):
        scroll_target(3, 0)


def test_ease_toward_no_time_no_move():
    assert ease_toward(2.0, 10.0, 0, 5) == 2.0


def test_ease_toward_moves_partway_without_overshoot():
    value = ease_toward(0.0, 10.0, 1.0, 1.0)
    assert value == pytest.approx(10 * (1 - 2.718281828**-1), rel=1e-6)
    assert 0.0 < value < 10.0


def test_ease_toward_reaches_target_given_time():
    assert ease_toward(0.0, 10.0, 10.0, 5.0) == pytest.approx(10.0, abs=1e-6)


def test_ease_toward_is_frame_rate_independent():
    one = ease_toward(0.0, 10.0, 1.0, 2.0)
    two = ease_toward(ease_toward(0.0, 10.0, 0.5, 2.0), 10.0, 0.5, 2.0)
    assert one == pytest.approx(two, rel=1e-9)
