import math

import pytest

from friday.island_logic import body_for, color_for, text_color_for
from friday.island_model import CAP_H, CAP_W, WRAP_W, IslandModel, mix_hex

LINE_H = 17.0


def fake_measure(text: str) -> tuple[float, float]:
    if not text:
        return 0.0, 0.0
    width = 8.0 * len(text)
    lines = max(1, math.ceil(width / WRAP_W))
    return min(width, float(WRAP_W)), LINE_H * lines


def make() -> IslandModel:
    return IslandModel(fake_measure, LINE_H)


def run(model: IslandModel, seconds: float, now: float = 0.0) -> float:
    step = 1 / 60
    for _ in range(int(round(seconds / step))):
        now += step
        model.tick(step, now)
    return now


def test_starts_collapsed_and_empty():
    m = make()
    assert m.body_w == CAP_W
    assert m.body_h == CAP_H
    assert m.visible_text == ""
    assert m.text_alpha == 0.0
    assert m.expand == 0.0


def test_mix_hex_endpoints_and_middle():
    assert mix_hex("#000000", "#ffffff", 0.0) == "#000000"
    assert mix_hex("#000000", "#ffffff", 1.0) == "#ffffff"
    assert mix_hex("#000000", "#ffffff", 0.5) == "#808080"


def test_short_text_keeps_the_collapsed_width():
    m = make()
    m.show_text("Привет")
    run(m, 1.0)
    assert m.body_w == pytest.approx(CAP_W)
    assert m.body_h == pytest.approx(35)


def test_long_text_opens_to_full_width_two_lines_and_scrolls():
    m = make()
    m.show_text("x" * 100)
    run(m, 1.0)
    assert m.body_w == pytest.approx(440)
    assert m.body_h == pytest.approx(52)
    assert m.scroll == pytest.approx(17)
    assert m.text_alpha == pytest.approx(1.0)


def test_clear_collapses_and_forgets_the_text():
    m = make()
    m.show_text("x" * 100)
    run(m, 1.0)
    m.clear_text()
    run(m, 1.0)
    assert m.body_w == pytest.approx(CAP_W)
    assert m.body_h == pytest.approx(CAP_H)
    assert m.visible_text == ""
    assert m.text_alpha == 0.0


def test_reveal_shows_a_growing_start_of_the_text_then_all_of_it():
    text = "Привет, босс. Расскажу про космос"
    m = make()
    m.start_reveal(text)
    assert m.visible_text == ""
    m.reveal_chunk(0, len(text), 1.0, 0.0)
    run(m, 3.0)
    assert m.visible_text
    assert text.startswith(m.visible_text)
    m.finish_reveal()
    assert m.visible_text == text


def test_chunk_is_ignored_when_the_text_is_not_revealed():
    m = make()
    m.show_text("Привет, босс")
    m.reveal_chunk(0, 5, 1.0, 0.0)
    assert m.visible_text == "Привет, босс"


def test_state_colour_fades_to_the_new_colour():
    m = make()
    m.set_state("listening")
    assert m.dot_color == color_for("idle")
    run(m, 0.5)
    assert m.dot_color == color_for("listening")


def test_theme_changes_the_colours():
    m = make()
    m.set_theme("black")
    assert m.body_color == body_for("black")
    assert m.text_color == text_color_for("black")
    run(m, 0.5)
    assert m.dot_color == color_for("idle", "black")


def test_pulse_runs_only_while_listening_or_speaking():
    m = make()
    assert m.pulse == 0.0
    m.set_state("listening")
    run(m, 0.65)
    assert m.pulse == pytest.approx(1.0, abs=0.02)
    m.set_state("idle")
    assert m.pulse == 0.0


def test_wave_eases_to_the_settings_of_the_state():
    m = make()
    assert m.wave_amplitude == pytest.approx(1.5)
    m.set_state("listening")
    run(m, 3.0)
    assert m.wave_amplitude == pytest.approx(3.0, abs=0.05)


def test_a_long_pause_between_ticks_is_clamped():
    m = make()
    m.tick(5.0, 5.0)
    assert m.phase == pytest.approx(0.1 * 1.2)


def test_line_height_must_be_positive():
    with pytest.raises(ValueError):
        IslandModel(fake_measure, 0)
