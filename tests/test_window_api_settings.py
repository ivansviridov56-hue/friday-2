from friday.settings_service import SettingsService
from friday.text_input import TextInput
from friday.ui_events import UiEventBus
from friday.window_api import WindowApi
from friday.window_controls import WindowControls


class FakeStore:
    def load(self):
        return {}

    def save(self, values):
        pass


def make():
    settings = SettingsService(UiEventBus(), FakeStore(), {})
    return WindowApi(TextInput(), WindowControls(), settings), settings


def make_without_settings():
    return WindowApi(TextInput(), WindowControls())


def test_get_settings_without_service_is_empty():
    api = make_without_settings()
    assert api.get_settings() == {}


def test_get_settings_forwards():
    api, settings = make()
    assert api.get_settings() == settings.snapshot()


def test_set_theme_forwards():
    api, settings = make()
    assert api.set_theme("black") is True
    assert settings.snapshot()["current"]["theme"] == "black"


def test_set_circles_forwards():
    api, settings = make()
    assert api.set_circles_style("dots") is True
    assert settings.snapshot()["current"]["circles"] == "dots"


def test_non_string_values_are_rejected():
    api, settings = make()
    assert api.set_theme(5) is False
    assert api.set_theme(None) is False
    assert api.set_circles_style(["dots"]) is False
    assert settings.snapshot()["current"] == {"theme": "classic", "circles": "classic"}


def test_set_without_service_returns_false():
    api = make_without_settings()
    assert api.set_theme("black") is False
    assert api.set_circles_style("dots") is False
