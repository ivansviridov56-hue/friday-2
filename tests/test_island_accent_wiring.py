import pytest

from friday.island_bridge import IslandBridge
from friday.island_model import IslandModel
from friday.island_process import IslandProcess
from friday.ui_events import AccentChanged, UiEventBus


class FakeIsland:
    def __init__(self) -> None:
        self.accents: list[str] = []

    def set_accent(self, accent: str) -> None:
        self.accents.append(accent)

    def __getattr__(self, name: str):
        return lambda *args, **kwargs: None


def _model() -> IslandModel:
    return IslandModel(lambda text: (0.0, 0.0), 20.0)


def _settle(model: IslandModel) -> None:
    # tick() caps one step at MAX_TICK, so walk through the whole colour fade
    for i in range(1, 21):
        model.tick(0.1, 0.1 * i)


# ---- bridge ----
def test_bridge_forwards_the_accent() -> None:
    bus = UiEventBus()
    island = FakeIsland()
    bridge = IslandBridge(bus, island)  # type: ignore[arg-type]
    bridge.start()
    bus.publish(AccentChanged("#4cc2ff", "#99ebff"))
    assert island.accents == ["#4cc2ff"]
    bridge.close()


def test_bridge_delivers_the_remembered_accent_on_start() -> None:
    bus = UiEventBus()
    bus.publish(AccentChanged("#4cc2ff", "#99ebff"))
    island = FakeIsland()
    bridge = IslandBridge(bus, island)  # type: ignore[arg-type]
    bridge.start()
    assert island.accents == ["#4cc2ff"]
    bridge.close()


# ---- model ----
def test_model_win11_idle_follows_the_accent() -> None:
    model = _model()
    model.set_theme("win11")
    model.set_accent("#4CC2FF")
    _settle(model)
    assert model.dot_color == "#4cc2ff"


def test_model_accent_before_theme_gives_the_same_result() -> None:
    model = _model()
    model.set_accent("#4cc2ff")
    model.set_theme("win11")
    _settle(model)
    assert model.dot_color == "#4cc2ff"


def test_model_other_theme_ignores_the_accent() -> None:
    model = _model()
    model.set_theme("classic")
    model.set_accent("#4cc2ff")
    _settle(model)
    assert model.dot_color == "#4c8dff"


def test_model_active_state_keeps_its_colour_in_win11() -> None:
    model = _model()
    model.set_theme("win11")
    model.set_accent("#4cc2ff")
    model.set_state("listening")
    _settle(model)
    assert model.dot_color == "#e5719b"


# ---- process ----
def test_process_sends_the_accent_line() -> None:
    process = IslandProcess(spawn=lambda: None)
    sent: list[str] = []
    process._send = sent.append  # type: ignore[method-assign]
    process.set_accent("#4cc2ff")
    assert sent == ["accent #4cc2ff\n"]


@pytest.mark.parametrize("bad", ["", "#4c c2ff"])
def test_process_ignores_empty_or_spaced_accent(bad: str) -> None:
    process = IslandProcess(spawn=lambda: None)
    sent: list[str] = []
    process._send = sent.append  # type: ignore[method-assign]
    process.set_accent(bad)
    assert sent == []
