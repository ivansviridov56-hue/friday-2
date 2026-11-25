import pytest

from friday.text_input import TextInput
from friday.window_api import WindowApi
from friday.window_controls import WindowControls


def make_api():
    received: list[str] = []
    text_input = TextInput()
    text_input.set_handler(lambda text: received.append(text) or True)
    calls: list[str] = []
    controls = WindowControls()
    controls.bind(
        lambda: calls.append("minimize"),
        lambda: calls.append("close"),
        lambda w, h: calls.append(f"resize {w}x{h}"),
    )
    return WindowApi(text_input, controls), received, calls


def test_submit_text_is_forwarded():
    api, received, _ = make_api()
    assert api.submit_text("привет") is True
    assert received == ["привет"]


@pytest.mark.parametrize("value", [None, 5, ["a"]])
def test_non_text_is_rejected(value):
    api, received, _ = make_api()
    assert api.submit_text(value) is False
    assert received == []


def test_minimize_is_forwarded():
    api, _, calls = make_api()
    assert api.minimize_window() is True
    assert calls == ["minimize"]


def test_close_is_forwarded():
    api, _, calls = make_api()
    assert api.close_window() is True
    assert calls == ["close"]


def test_public_methods_are_the_whole_page_api():
    names = {name for name in dir(WindowApi) if not name.startswith("_")}
    assert names == {
        "submit_text",
        "minimize_window",
        "close_window",
        "resize_window",
        "get_settings",
        "set_theme",
        "set_transparency",
        "set_circles_style",
        "set_island_look",
    }


def test_resize_is_forwarded():
    api, _, calls = make_api()
    assert api.resize_window(500, 600) is True
    assert calls == ["resize 500x600"]


@pytest.mark.parametrize("value", [None, "500", True, float("nan")])
def test_resize_rejects_non_numbers(value):
    api, _, calls = make_api()
    assert api.resize_window(value, 600) is False
    assert calls == []


def test_set_transparency_is_forwarded():
    from friday.settings_service import SettingsService
    from friday.ui_events import UiEventBus

    class Store:
        def load(self):
            return {}

        def save(self, values):
            pass

    service = SettingsService(UiEventBus(), Store(), {})
    api = WindowApi(TextInput(), WindowControls(), service)
    assert api.set_transparency(30) is True
    assert service.snapshot()["percents"]["classic"] == 30


@pytest.mark.parametrize("value", [None, "30", True, float("nan"), 101])
def test_set_transparency_rejects_bad_values(value):
    api, _, _ = make_api()
    assert api.set_transparency(value) is False
