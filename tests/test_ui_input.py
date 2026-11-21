from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "friday" / "ui"


def test_input_is_a_growing_text_area():
    html = (UI / "index.html").read_text(encoding="utf-8")
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert '<textarea id="text-input"' in html
    assert "fitInput" in js


def test_enter_sends_and_shift_enter_makes_a_new_line():
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert "shiftKey" in js
    assert "requestSubmit" in js


def test_input_follows_the_state_colour():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "caret-color: var(--c1)" in css
    assert "@keyframes nudge" in css


def test_multiline_input_fades_at_the_edges():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "mask-image: linear-gradient" in css
    assert "#composer { border-radius: 26px;" in css


def test_composer_is_compact_until_hover_or_focus():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "#composer:hover" in css
    assert "flex: 0 1 260px" in css


def test_placeholder_does_not_follow_the_state():
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert "textInput.placeholder" not in js


def test_island_animates_its_height_not_the_text_area():
    js = (UI / "app.js").read_text(encoding="utf-8")
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "composer.style.height" in js
    assert "height 0.22s" in css


def test_island_is_clipped_not_scrollable():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "overflow: clip" in css
