from friday.island_logic import ease_width, target_body_width


def test_short_text_keeps_the_collapsed_width():
    assert target_body_width(40, 150, 440, 40, 18) == 150


def test_text_width_adds_the_paddings():
    assert target_body_width(200, 150, 440, 40, 18) == 258


def test_long_text_is_capped_at_the_maximum():
    assert target_body_width(900, 150, 440, 40, 18) == 440


def test_empty_text_gives_the_collapsed_width():
    assert target_body_width(0, 150, 440, 40, 18) == 150


def test_ease_moves_toward_the_target_without_overshoot():
    value = ease_width(150.0, 300.0, 0.05, 14.0)
    assert 150.0 < value < 300.0


def test_ease_works_downwards_too():
    value = ease_width(300.0, 150.0, 0.05, 14.0)
    assert 150.0 < value < 300.0


def test_ease_snaps_when_very_close():
    assert ease_width(299.9, 300.0, 0.01, 14.0) == 300.0


def test_ease_without_time_does_not_move():
    assert ease_width(200.0, 300.0, 0.0, 14.0) == 200.0
