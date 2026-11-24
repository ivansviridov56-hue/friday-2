from friday.island_logic import visible_lines_height


def test_no_text_gives_no_height():
    assert visible_lines_height(0, 16, 2) == 0


def test_one_line_keeps_its_height():
    assert visible_lines_height(16, 16, 2) == 16


def test_two_lines_keep_their_height():
    assert visible_lines_height(32, 16, 2) == 32


def test_more_lines_are_capped():
    assert visible_lines_height(80, 16, 2) == 32
