from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "friday" / "ui"


def test_page_has_the_dock_and_the_music_circle():
    html = (UI / "index.html").read_text(encoding="utf-8")
    for element_id in ("dock", "music-orb"):
        assert f'id="{element_id}"' in html


def test_layout_is_styled():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    for selector in ("#dock", "#music-orb", "#composer"):
        assert selector in css


def test_extra_decorations_are_gone():
    html = (UI / "index.html").read_text(encoding="utf-8")
    assert 'id="hint"' not in html
    assert 'class="dots"' not in html


def test_inner_circles_are_blurred():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert ".c1, .c2, .c3 { filter: blur(" in css


def test_background_has_a_noise_layer():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "#bg-layer::after" in css
