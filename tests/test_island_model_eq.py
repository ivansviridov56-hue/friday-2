from friday.island_model import IslandModel


def _model():
    return IslandModel(lambda text: (0.0, 0.0), 16.0)


def _feed(model, seconds, start=0.0, levels=None, dt=0.02):
    now = start
    for _ in range(round(seconds / dt)):
        now += dt
        if levels is not None:
            model.set_eq(levels, now)
        model.tick(dt, now)
    return now


def test_starts_without_the_equalizer():
    model = _model()
    assert model.eq_mix == 0.0
    assert model.eq_levels == []


def test_levels_fade_the_edge_in():
    model = _model()
    _feed(model, 1.2, levels=[0.5] * 16)
    assert model.eq_mix == 1.0
    assert model.eq_levels == [0.5] * 16


def test_the_blend_is_between_while_fading():
    model = _model()
    _feed(model, 0.2, levels=[0.5] * 16)
    assert 0.0 < model.eq_mix < 1.0


def test_without_new_levels_the_edge_returns_to_the_wave():
    model = _model()
    now = _feed(model, 1.2, levels=[0.5] * 16)
    _feed(model, 2.0, start=now)
    assert model.eq_mix == 0.0
    assert max(model.eq_levels) < 0.01


def test_levels_are_clamped_and_empty_levels_are_ignored():
    model = _model()
    model.set_eq([], 0.0)
    assert model.eq_levels == []
    model.set_eq([-1.0, 2.0], 0.0)
    assert model.eq_levels == [0.0, 1.0]
