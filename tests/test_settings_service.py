from friday.settings_service import SettingsService
from friday.ui_events import (
    CirclesStyleChanged,
    ThemeChanged,
    UiEventBus,
    TransparencyChanged,
)


class FakeStore:
    def __init__(self, data=None):
        self.data = data or {}
        self.saved = []
        self.fail = False

    def load(self):
        return dict(self.data)

    def save(self, values):
        if self.fail:
            raise OSError("disk full")
        self.saved.append(dict(values))


def make(data=None, env=None):
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    store = FakeStore(data)
    return SettingsService(bus, store, env or {}), store, got


def test_env_is_used_when_nothing_saved():
    service, _, _ = make(env={"THEME": "black", "CIRCLES": "dots"})
    assert service.snapshot()["current"] == {
        "theme": "black",
        "circles": "dots",
        "island_look": "dot",
    }


def test_saved_choice_wins_over_env():
    service, _, _ = make(
        data={"theme": "windows"}, env={"THEME": "black", "CIRCLES": "dots"}
    )
    assert service.snapshot()["current"] == {
        "theme": "windows",
        "circles": "dots",
        "island_look": "dot",
    }


def test_unknown_env_gives_defaults():
    service, _, _ = make(env={"THEME": "pink", "CIRCLES": "sparkles"})
    assert service.snapshot()["current"] == {
        "theme": "classic",
        "circles": "classic",
        "island_look": "dot",
    }


def test_publish_initial_sends_all_four():
    service, _, got = make(env={"THEME": "black", "CIRCLES": "blobs"})
    service.publish_initial()
    assert CirclesStyleChanged("blobs") in got
    assert ThemeChanged("black") in got
    assert TransparencyChanged(0) in got
    assert len(got) == 4


def test_set_theme_applies_and_saves():
    service, store, got = make()
    assert service.set_theme("windows") is True
    assert got == [ThemeChanged("windows"), TransparencyChanged(0)]
    assert store.saved[-1]["theme"] == "windows"
    assert service.snapshot()["current"]["theme"] == "windows"


def test_set_circles_applies_and_saves():
    service, store, got = make()
    assert service.set_circles("equalizer") is True
    assert got == [CirclesStyleChanged("equalizer")]
    assert store.saved[-1]["circles"] == "equalizer"


def test_unknown_value_is_rejected():
    service, store, got = make()
    assert service.set_theme("pink") is False
    assert service.set_circles("sparkles") is False
    assert got == []
    assert store.saved == []
    assert service.snapshot()["current"] == {
        "theme": "classic",
        "circles": "classic",
        "island_look": "dot",
    }


def test_save_failure_still_applies():
    service, store, got = make()
    store.fail = True
    assert service.set_theme("black") is True
    assert got == [ThemeChanged("black"), TransparencyChanged(0)]
    assert service.snapshot()["current"]["theme"] == "black"


def test_snapshot_lists_choices():
    service, _, _ = make()
    snap = service.snapshot()
    assert snap["themes"] == ["classic", "windows", "black", "win11"]
    assert snap["circles"] == ["classic", "blobs", "equalizer", "dots"]


def test_default_percents_in_snapshot():
    service, _, _ = make()
    assert service.snapshot()["percents"] == {
        "classic": 0,
        "windows": 0,
        "black": 0,
        "win11": 40,
    }


def test_set_transparency_applies_and_saves_for_current_theme():
    service, store, got = make(env={"THEME": "black"})
    assert service.set_transparency(35) is True
    assert got == [TransparencyChanged(35)]
    assert store.saved[-1]["transparency"] == {"black": 35}
    assert service.snapshot()["percents"]["black"] == 35
    assert service.snapshot()["percents"]["classic"] == 0


def test_each_theme_keeps_its_own_percent():
    service, _, got = make()
    service.set_transparency(20)
    service.set_theme("win11")
    service.set_transparency(70)
    got.clear()
    service.set_theme("classic")
    assert got == [ThemeChanged("classic"), TransparencyChanged(20)]
    service.set_theme("win11")
    assert got[-1] == TransparencyChanged(70)


def test_theme_change_always_sends_the_percent_of_the_new_theme():
    service, _, got = make()
    service.set_theme("windows")
    assert got == [ThemeChanged("windows"), TransparencyChanged(0)]


def test_bad_percent_is_rejected():
    service, store, got = make()
    for bad in (-1, 101, None, "5", True, float("nan")):
        assert service.set_transparency(bad) is False
    assert got == []
    assert store.saved == []


def test_saved_percents_are_loaded():
    service, _, _ = make(data={"theme": "win11", "transparency": {"win11": 80}})
    assert service.snapshot()["percents"]["win11"] == 80


def test_theme_save_keeps_percents():
    service, store, _ = make()
    service.set_transparency(15)
    service.set_theme("black")
    assert store.saved[-1]["transparency"] == {"classic": 15}
