from friday.settings_service import SettingsService
from friday.ui_events import CirclesStyleChanged, ThemeChanged, UiEventBus


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
    assert service.snapshot()["current"] == {"theme": "black", "circles": "dots"}


def test_saved_choice_wins_over_env():
    service, _, _ = make(
        data={"theme": "windows"}, env={"THEME": "black", "CIRCLES": "dots"}
    )
    assert service.snapshot()["current"] == {"theme": "windows", "circles": "dots"}


def test_unknown_env_gives_defaults():
    service, _, _ = make(env={"THEME": "pink", "CIRCLES": "sparkles"})
    assert service.snapshot()["current"] == {"theme": "classic", "circles": "classic"}


def test_publish_initial_sends_both():
    service, _, got = make(env={"THEME": "black", "CIRCLES": "blobs"})
    service.publish_initial()
    assert CirclesStyleChanged("blobs") in got
    assert ThemeChanged("black") in got
    assert len(got) == 2


def test_set_theme_applies_and_saves():
    service, store, got = make()
    assert service.set_theme("windows") is True
    assert got == [ThemeChanged("windows")]
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
    assert service.snapshot()["current"] == {"theme": "classic", "circles": "classic"}


def test_save_failure_still_applies():
    service, store, got = make()
    store.fail = True
    assert service.set_theme("black") is True
    assert got == [ThemeChanged("black")]
    assert service.snapshot()["current"]["theme"] == "black"


def test_snapshot_lists_choices():
    service, _, _ = make()
    snap = service.snapshot()
    assert snap["themes"] == ["classic", "windows", "black"]
    assert snap["circles"] == ["classic", "blobs", "equalizer", "dots"]
