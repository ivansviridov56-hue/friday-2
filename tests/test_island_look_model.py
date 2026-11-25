from friday.island_looks import look_shapes
from friday.island_model import IslandModel


def fake_measure(text: str) -> tuple[float, float]:
    return (len(text) * 7.0, 17.0)


def make() -> IslandModel:
    return IslandModel(fake_measure, 17.0)


def test_the_default_look_is_the_dot():
    m = make()
    assert m.look == "dot"
    assert len(m.icon_shapes) == 1


def test_set_look_changes_the_shapes():
    m = make()
    m.set_look("eyes")
    assert m.look == "eyes"
    assert len(m.icon_shapes) == 2
    m.set_look("equalizer")
    assert len(m.icon_shapes) == 4


def test_an_unknown_look_falls_back_to_the_dot():
    m = make()
    m.set_look("eyes")
    m.set_look("nope")
    assert m.look == "dot"


def test_the_icon_time_moves_with_ticks():
    m = make()
    m.set_look("equalizer")
    m.set_state("listening")
    before = m.icon_shapes
    m.tick(0.05, 0.05)
    assert m.icon_shapes != before


def test_the_icon_gets_the_state_time_and_pulse():
    m = make()
    m.set_state("speaking")
    m.tick(0.1, 0.1)
    assert m.pulse > 0
    assert m.icon_shapes == look_shapes("dot", "speaking", 0.1, m.pulse)


def test_a_long_pause_between_ticks_is_clamped():
    m = make()
    m.tick(5.0, 5.0)
    assert m.icon_shapes == look_shapes("dot", "idle", 0.1, 0.0)


def test_the_look_survives_a_state_change():
    m = make()
    m.set_look("eyes")
    m.set_state("thinking")
    assert m.look == "eyes"
