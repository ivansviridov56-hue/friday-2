import pytest

from friday.word_fade import (
    FADE_SECONDS,
    add_span,
    build_markup,
    fade_alpha,
    live_spans,
)


def color_at(alpha: float) -> str:
    return f"c{alpha:.2f}"


def test_alpha_starts_at_zero_and_ends_at_one():
    assert fade_alpha(0.0) == 0.0
    assert fade_alpha(FADE_SECONDS) == pytest.approx(1.0)


def test_alpha_is_half_in_the_middle():
    assert fade_alpha(FADE_SECONDS / 2) == pytest.approx(0.5)


def test_alpha_is_clamped():
    assert fade_alpha(-1.0) == 0.0
    assert fade_alpha(10.0) == 1.0


def test_zero_fade_time_means_full_colour():
    assert fade_alpha(0.0, 0.0) == 1.0


def test_add_span_ignores_an_empty_span():
    assert add_span([], 3, 3, 0.0) == []


def test_add_span_appends():
    assert add_span([(0, 2, 0.0)], 2, 5, 1.0) == [(0, 2, 0.0), (2, 5, 1.0)]


def test_live_spans_drops_finished_ones():
    spans = [(0, 2, 0.0), (2, 5, 0.9)]
    assert live_spans(spans, 1.0, 1.0) == [(2, 5, 0.9)]


def test_markup_without_spans_is_the_plain_text():
    assert build_markup("ab cd", [], 0.0, color_at) == "ab cd"


def test_markup_escapes_html():
    assert build_markup("a < b & c > d", [], 0.0, color_at) == "a &lt; b &amp; c &gt; d"


def test_markup_turns_a_newline_into_a_break():
    assert build_markup("a\nb", [], 0.0, color_at) == "a<br>b"


def test_markup_colours_a_fading_span():
    out = build_markup("ab cd", [(2, 5, 0.0)], 0.5, color_at, seconds=1.0)
    assert out == 'ab<font color="c0.50"> cd</font>'


def test_markup_keeps_the_text_before_a_span():
    out = build_markup("ab cd ef", [(5, 8, 0.0)], 0.0, color_at, seconds=1.0)
    assert out == 'ab cd<font color="c0.00"> ef</font>'


def test_markup_with_two_words_in_the_tail():
    spans = [(2, 5, 0.0), (5, 8, 0.6)]
    out = build_markup("ab cd ef", spans, 0.6, color_at, seconds=1.0)
    assert out == 'ab<font color="c0.65"> cd</font><font color="c0.00"> ef</font>'


def test_markup_drops_a_finished_span():
    out = build_markup("ab cd", [(2, 5, 0.0)], 1.0, color_at, seconds=1.0)
    assert out == "ab cd"


def test_markup_clips_a_span_past_the_end():
    out = build_markup("ab cd", [(2, 50, 0.0)], 0.0, color_at, seconds=1.0)
    assert out == 'ab<font color="c0.00"> cd</font>'


def test_markup_does_not_repeat_text_of_overlapping_spans():
    spans = [(0, 5, 0.0), (3, 8, 0.0)]
    out = build_markup("abcdefgh", spans, 0.0, color_at, seconds=1.0)
    assert out == '<font color="c0.00">abcde</font><font color="c0.00">fgh</font>'
