import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QML = ROOT / "friday" / "ui" / "island.qml"
SOURCE = ROOT / "friday" / "island_quick.py"


def test_the_qml_page_exists():
    assert QML.is_file()


def test_every_backend_name_used_by_the_page_is_defined():
    names = set(re.findall(r"backend\.(\w+)", QML.read_text(encoding="utf-8")))
    names.discard("frame")
    source = SOURCE.read_text(encoding="utf-8")
    missing = [n for n in sorted(names) if f"def {n}(" not in source]
    assert missing == []


def test_the_frame_slot_the_page_calls_exists():
    assert "def frame(" in SOURCE.read_text(encoding="utf-8")


def test_the_page_is_driven_by_the_frame_animation():
    assert "FrameAnimation" in QML.read_text(encoding="utf-8")
