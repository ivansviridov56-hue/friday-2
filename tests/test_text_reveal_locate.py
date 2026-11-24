from friday.text_reveal import locate_chunk

TEXT = "Hello there. How are you doing today?"


def test_locate_finds_chunk():
    assert locate_chunk(TEXT, "Hello there.") == (0, 12)


def test_locate_starts_at_pos():
    assert locate_chunk("Yes. Yes.", "Yes.", 1) == (5, 9)


def test_locate_missing_chunk_is_none():
    assert locate_chunk(TEXT, "Looking at the screen.") is None


def test_locate_empty_chunk_is_none():
    assert locate_chunk(TEXT, "") is None


def test_locate_negative_pos_is_treated_as_zero():
    assert locate_chunk(TEXT, "Hello", -5) == (0, 5)


def test_locate_pos_past_the_end_is_none():
    assert locate_chunk(TEXT, "Hello", 100) is None
