"""The page fades in once the theme has arrived (no abrupt appearance)."""

import re
from pathlib import Path

CSS = (
    Path(__file__).resolve().parent.parent / "friday" / "ui" / "styles.css"
).read_text(encoding="utf-8")


def test_page_is_transparent_until_theme_arrives() -> None:
    assert re.search(r":root:not\(\[data-theme\]\) body\s*\{\s*opacity:\s*0;", CSS)


def test_page_does_not_use_visibility_hidden_for_the_theme_wait() -> None:
    assert not re.search(
        r":root:not\(\[data-theme\]\) body\s*\{\s*visibility:\s*hidden", CSS
    )


def test_body_fades_in() -> None:
    assert re.search(r"(^|\n)body\s*\{\s*transition:\s*opacity\s+0\.5s", CSS)
