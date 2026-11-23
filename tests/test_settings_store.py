import json

from friday.settings_store import SettingsStore


def test_missing_file_gives_empty(tmp_path):
    assert SettingsStore(tmp_path / "settings.json").load() == {}


def test_save_then_load(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save({"theme": "black", "circles": "dots"})
    assert store.load() == {"theme": "black", "circles": "dots"}


def test_corrupt_file_gives_empty(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    assert SettingsStore(path).load() == {}


def test_non_object_json_gives_empty(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert SettingsStore(path).load() == {}


def test_unknown_keys_and_values_are_dropped_on_load(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"theme": "pink", "circles": "dots", "volume": "loud", "x": 5}),
        encoding="utf-8",
    )
    assert SettingsStore(path).load() == {"circles": "dots"}


def test_save_drops_unknown_values(tmp_path):
    path = tmp_path / "settings.json"
    SettingsStore(path).save({"theme": "pink", "circles": "blobs"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"circles": "blobs"}


def test_save_creates_the_folder(tmp_path):
    path = tmp_path / "data" / "settings.json"
    SettingsStore(path).save({"theme": "windows"})
    assert path.exists()


def test_bad_encoding_gives_empty(tmp_path):
    path = tmp_path / "settings.json"
    path.write_bytes(b"\xff\xfe\x00\x80")
    assert SettingsStore(path).load() == {}


def test_no_temp_file_is_left(tmp_path):
    path = tmp_path / "settings.json"
    SettingsStore(path).save({"theme": "black"})
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_transparency_round_trip(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save({"theme": "black", "transparency": {"black": 25, "win11": 70}})
    assert store.load() == {
        "theme": "black",
        "transparency": {"black": 25, "win11": 70},
    }


def test_bad_transparency_is_dropped_on_load(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"transparency": {"classic": 999, "pink": 10, "black": "x"}}),
        encoding="utf-8",
    )
    assert SettingsStore(path).load() == {}


def test_transparency_that_is_not_an_object_is_dropped(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"transparency": 40}), encoding="utf-8")
    assert SettingsStore(path).load() == {}


def test_old_file_without_transparency_still_loads(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "win11"}), encoding="utf-8")
    assert SettingsStore(path).load() == {"theme": "win11"}
