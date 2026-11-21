from friday.window_controls import WindowControls

import pytest


def make_controls():
    calls: list[str] = []
    controls = WindowControls()
    controls.bind(lambda: calls.append("minimize"), lambda: calls.append("close"))
    return controls, calls


def test_unbound_controls_do_nothing():
    controls = WindowControls()
    assert controls.minimize() is False
    assert controls.close() is False


def test_minimize_calls_the_bound_action():
    controls, calls = make_controls()
    assert controls.minimize() is True
    assert calls == ["minimize"]


def test_close_calls_the_bound_action():
    controls, calls = make_controls()
    assert controls.close() is True
    assert calls == ["close"]


def test_broken_action_does_not_raise():
    controls = WindowControls()

    def broken():
        raise RuntimeError("boom")

    controls.bind(broken, broken)
    assert controls.minimize() is False
    assert controls.close() is False


def test_unbind_stops_the_actions():
    controls, calls = make_controls()
    controls.unbind()
    assert controls.minimize() is False
    assert controls.close() is False
    assert calls == []


def test_bind_again_replaces_the_actions():
    controls, calls = make_controls()
    other: list[str] = []
    controls.bind(lambda: other.append("m"), lambda: other.append("c"))
    controls.minimize()
    controls.close()
    assert calls == []
    assert other == ["m", "c"]


def make_resizable(min_size=(320, 420), max_size=(1000, 800)):
    sizes: list[tuple[int, int]] = []
    controls = WindowControls(min_size=min_size, max_size=max_size)
    controls.bind(lambda: None, lambda: None, lambda w, h: sizes.append((w, h)))
    return controls, sizes


def test_resize_passes_the_size_on():
    controls, sizes = make_resizable()
    assert controls.resize(500.7, 600.2) is True
    assert sizes == [(500, 600)]


def test_resize_is_clamped_to_the_minimum():
    controls, sizes = make_resizable()
    controls.resize(100, 100)
    assert sizes == [(320, 420)]


def test_resize_is_clamped_to_the_maximum():
    controls, sizes = make_resizable()
    controls.resize(5000, 5000)
    assert sizes == [(1000, 800)]


def test_resize_without_an_action_does_nothing():
    assert WindowControls().resize(500, 600) is False
    controls = WindowControls()
    controls.bind(lambda: None, lambda: None)
    assert controls.resize(500, 600) is False


def test_broken_resize_does_not_raise():
    controls = WindowControls()

    def broken(width, height):
        raise RuntimeError("boom")

    controls.bind(lambda: None, lambda: None, broken)
    assert controls.resize(500, 600) is False


def test_bad_limits_are_a_mistake():
    with pytest.raises(ValueError):
        WindowControls(min_size=(0, 10))
    with pytest.raises(ValueError):
        WindowControls(min_size=(500, 500), max_size=(400, 600))
