from friday.island_model import IslandModel, mix_hex
from friday.word_fade import FADE_SECONDS, fade_alpha

LINE_H = 17.0
TEXT = "one two three"


def fake_measure(text: str) -> tuple[float, float]:
    return (len(text) * 7.0, LINE_H)


def make() -> IslandModel:
    m = IslandModel(fake_measure, LINE_H)
    m.start_reveal(TEXT)
    return m


def colour(m: IslandModel, alpha: float) -> str:
    return mix_hex(m.body_color, m.text_color, alpha)


def test_markup_is_empty_before_any_word():
    assert make().markup == ""


def test_a_new_word_starts_in_the_body_colour():
    m = make()
    m.reveal_chunk(0, 13, 100.0, 0.0)
    m.tick(0.01, 50.0)
    assert m.markup == f'<font color="{colour(m, 0.0)}">one two</font>'


def test_a_word_fades_to_the_plain_text_colour():
    m = make()
    m.reveal_chunk(0, 13, 100.0, 0.0)
    m.tick(0.01, 50.0)
    m.tick(0.01, 50.0 + FADE_SECONDS + 0.01)
    assert m.markup == "one two"


def test_the_colour_is_between_in_the_middle_of_the_fade():
    m = make()
    m.reveal_chunk(0, 13, 100.0, 0.0)
    m.tick(0.01, 50.0)
    m.tick(0.01, 50.0 + FADE_SECONDS / 2)
    assert m.markup == f'<font color="{colour(m, 0.5)}">one two</font>'


def test_two_words_in_the_tail_have_different_colours():
    m = make()
    m.reveal_chunk(0, 13, 1.0, 0.0)
    m.tick(0.01, 0.5)
    m.tick(0.01, 0.6)
    m.tick(0.01, 0.7)
    first = colour(m, fade_alpha(0.7 - 0.5))
    second = colour(m, 0.0)
    assert m.markup == (
        f'<font color="{first}">one two</font><font color="{second}"> three</font>'
    )


def test_finishing_the_reveal_fades_the_rest_in():
    m = make()
    m.reveal_chunk(0, 13, 100.0, 0.0)
    m.tick(0.01, 50.0)
    m.finish_reveal()
    assert m.visible_text == TEXT
    assert m.markup.endswith(f'<font color="{colour(m, 0.0)}"> three</font>')


def test_text_shown_at_once_has_no_fade():
    m = IslandModel(fake_measure, LINE_H)
    m.show_text("hello")
    assert m.markup == "hello"


def test_markup_escapes_the_text():
    m = IslandModel(fake_measure, LINE_H)
    m.show_text("a < b & c")
    assert m.markup == "a &lt; b &amp; c"


def test_a_new_reveal_forgets_the_old_fade():
    m = make()
    m.reveal_chunk(0, 13, 100.0, 0.0)
    m.tick(0.01, 50.0)
    m.start_reveal("x y")
    assert m.markup == ""
