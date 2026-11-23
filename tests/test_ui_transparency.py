from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "friday" / "ui"


def read(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def test_panel_has_the_slider_and_its_label():
    html = read("index.html")
    assert 'id="transparency"' in html
    assert 'type="range"' in html
    assert 'id="transparency-value"' in html


def test_page_does_not_paint_over_the_blur():
    css = read("styles.css")
    assert "color-mix(in srgb, var(--bg)" not in css


def test_slider_saves_through_the_api_on_release():
    js = read("app.js")
    assert "set_transparency" in js
    assert '"change"' in js


def test_set_transparency_moves_the_slider():
    js = read("app.js")
    assert "setTransparency(percent)" in js
    assert "transparency-value" in js
