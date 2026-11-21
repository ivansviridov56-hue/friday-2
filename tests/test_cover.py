import base64
import json

from friday.cover_data import to_data_url
from friday.ui_bridge import UiBridge
from friday.ui_events import CoverChanged, UiEventBus

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 8


def test_png_becomes_data_url():
    url = to_data_url(PNG)
    assert url == "data:image/png;base64," + base64.b64encode(PNG).decode()


def test_jpeg_becomes_data_url():
    url = to_data_url(JPG)
    assert url is not None
    assert url.startswith("data:image/jpeg;base64,")


def test_empty_and_unknown_data_give_none():
    assert to_data_url(None) is None
    assert to_data_url(b"") is None
    assert to_data_url(b"not an image") is None


def test_bridge_sends_cover_to_page():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(CoverChanged("data:image/png;base64,AAA"))
    assert scripts == ['window.fridayUi.setCover("data:image/png;base64,AAA")']


def test_bridge_sends_null_to_hide_cover():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.mark_ready()
    bridge.on_event(CoverChanged(None))
    assert scripts == ["window.fridayUi.setCover(null)"]


def test_cover_before_page_is_loaded_is_queued():
    scripts = []
    bridge = UiBridge(scripts.append)
    bridge.on_event(CoverChanged("data:image/png;base64,AAA"))
    assert scripts == []
    bridge.mark_ready()
    assert json.dumps("data:image/png;base64,AAA") in scripts[0]


def test_bus_delivers_cover_event():
    bus = UiEventBus()
    got = []
    bus.subscribe(got.append)
    bus.publish(CoverChanged(None))
    assert got == [CoverChanged(None)]
