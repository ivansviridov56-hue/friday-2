from friday.island_looks import DEFAULT_LOOK, LOOKS
from friday.settings_service import SettingsService
from friday.settings_store import SettingsStore
from friday.ui_events import IslandLookChanged, UiEventBus
from friday.window_api import WindowApi
from typing import Any

NOTHING: Any = (
    None  # the API methods under test never touch the text input or the controls
)


class MemoryStore:
    def __init__(self, saved=None):
        self.saved = saved or {}
        self.writes = []

    def load(self):
        return dict(self.saved)

    def save(self, values):
        self.writes.append(dict(values))


def make(saved=None):
    bus = UiEventBus()
    store = MemoryStore(saved)
    service = SettingsService(bus, store, {})
    got = []
    bus.subscribe(got.append)
    return service, store, got


def test_the_default_look_and_the_list_for_the_panel():
    service, _, _ = make()
    snap = service.snapshot()
    assert snap["current"]["island_look"] == DEFAULT_LOOK
    assert snap["island_looks"] == list(LOOKS)


def test_a_saved_look_is_used():
    service, _, _ = make({"island_look": "eyes"})
    assert service.snapshot()["current"]["island_look"] == "eyes"


def test_the_starting_look_is_published():
    service, _, got = make({"island_look": "eyes"})
    service.publish_initial()
    assert IslandLookChanged("eyes") in got


def test_choosing_a_look_publishes_and_saves_it():
    service, store, got = make()
    assert service.set_island_look("equalizer") is True
    assert IslandLookChanged("equalizer") in got
    assert store.writes[-1]["island_look"] == "equalizer"
    assert service.snapshot()["current"]["island_look"] == "equalizer"


def test_an_unknown_look_is_refused():
    service, store, got = make()
    assert service.set_island_look("nope") is False
    assert got == []
    assert store.writes == []


def test_the_look_survives_a_round_trip_through_the_file(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save({"island_look": "eyes"})
    assert store.load()["island_look"] == "eyes"


def test_an_unknown_look_in_the_file_is_dropped(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save({"island_look": "nope"})
    assert "island_look" not in store.load()


def test_the_page_can_choose_a_look():
    service, _, _ = make()
    api = WindowApi(NOTHING, NOTHING, service)
    assert api.set_island_look("eyes") is True
    assert api.get_settings()["current"]["island_look"] == "eyes"


def test_the_api_refuses_bad_values():
    service, _, _ = make()
    api = WindowApi(NOTHING, NOTHING, service)
    assert api.set_island_look(5) is False
    assert api.set_island_look(None) is False
    assert api.set_island_look("nope") is False


def test_the_api_without_settings_refuses():
    assert WindowApi(NOTHING, NOTHING).set_island_look("eyes") is False
