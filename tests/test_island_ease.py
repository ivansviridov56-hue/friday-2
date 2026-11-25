import pytest

from friday.island_logic import ease_width


def test_tail_does_not_crawl():
    assert ease_width(0.0, 10.0, 0.01, 1.0) == pytest.approx(0.3)


def test_never_overshoots():
    assert ease_width(0.0, 0.6, 1.0, 0.01) == 0.6
