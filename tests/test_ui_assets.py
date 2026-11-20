from pathlib import Path

import pytest

from friday.ui_events import State

UI_DIR = Path(__file__).resolve().parent.parent / "friday" / "ui"


@pytest.mark.parametrize("state", list(State))
def test_every_state_has_a_css_rule(state):
    css = (UI_DIR / "styles.css").read_text(encoding="utf-8")
    assert f"body.state-{state.value}" in css


def test_page_links_its_assets():
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html
    assert 'src="app.js"' in html


def test_script_exposes_the_bridge_api():
    js = (UI_DIR / "app.js").read_text(encoding="utf-8")
    assert "window.fridayUi" in js
    assert "setState" in js
    assert "addMessage" in js


def test_script_exposes_set_level():
    js = (UI_DIR / "app.js").read_text(encoding="utf-8")
    assert "setLevel" in js
    assert "--lvl" in js


def test_circles_use_the_level_variable():
    css = (UI_DIR / "styles.css").read_text(encoding="utf-8")
    assert "var(--lvl)" in css
