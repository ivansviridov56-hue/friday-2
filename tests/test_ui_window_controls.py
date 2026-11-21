from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "friday" / "ui"


def test_header_has_a_drag_region():
    html = (UI / "index.html").read_text(encoding="utf-8")
    assert 'class="drag-strip pywebview-drag-region"' in html


def test_page_has_window_buttons():
    html = (UI / "index.html").read_text(encoding="utf-8")
    for element_id in ("btn-minimize", "btn-close"):
        assert f'id="{element_id}"' in html


def test_script_calls_the_window_api():
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert "minimize_window" in js
    assert "close_window" in js


def test_window_is_frameless_with_manual_drag():
    source = (ROOT / "friday" / "window.py").read_text(encoding="utf-8")
    assert "frameless=True" in source
    assert "easy_drag=False" in source


def test_page_has_resize_handles():
    html = (UI / "index.html").read_text(encoding="utf-8")
    for element_id in ("resize-right", "resize-bottom", "resize-corner"):
        assert f'id="{element_id}"' in html


def test_script_resizes_through_the_api():
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert "resize_window" in js
