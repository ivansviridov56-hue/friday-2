from friday.island_logic import scroll_for


def test_text_that_fits_does_not_scroll():
    assert scroll_for(32, 16, 2) == 0


def test_one_extra_line_scrolls_by_one_line():
    assert scroll_for(48, 16, 2) == 16


def test_many_extra_lines_scroll_by_all_of_them():
    assert scroll_for(96, 16, 2) == 64
