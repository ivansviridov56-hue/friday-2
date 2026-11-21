from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "friday" / "ui"


def test_page_has_the_composer():
    html = (UI / "index.html").read_text(encoding="utf-8")
    for element_id in ("composer", "text-input", "send"):
        assert f'id="{element_id}"' in html


def test_script_sends_text_through_the_python_api():
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert "submit_text" in js


def test_composer_is_styled():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "#composer" in css
    assert "#text-input" in css
