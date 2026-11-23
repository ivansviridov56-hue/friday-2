from friday.backdrop_logic import (
    CHANGE_STEPS,
    TINT_COLORS,
    make_tint,
    opacity_for,
    tint_for,
)
from friday.backdrop_tint import BackdropTint
from friday.theme import THEMES
from friday.ui_events import State, StateChanged, ThemeChanged, TransparencyChanged


def run(*events):
    got = []
    tint = BackdropTint(lambda color, opacity: got.append((color, opacity)))
    for event in events:
        tint.on_event(event)
    return got


def test_every_theme_has_a_tint_colour():
    assert set(TINT_COLORS) == set(THEMES)


def test_unknown_theme_gets_the_default_colour():
    assert tint_for("pink") == "#202020"


def test_opacity_follows_the_slider():
    assert opacity_for(0) == 1.0
    assert opacity_for(40) == 0.6
    assert opacity_for(100) == 0.0


def test_percent_is_clamped():
    assert opacity_for(150) == 0.0
    assert opacity_for(-5) == 1.0


def test_make_tint_alpha_follows_opacity():
    assert make_tint("#000000", 0.0) >> 24 == 0
    assert make_tint("#000000", 1.0) >> 24 == 255


def test_change_is_one_step_with_extended_glass():
    assert [(s.extend, s.delay) for s in CHANGE_STEPS] == [(True, 0.0)]


def test_win11_default_is_the_old_tint():
    assert run(ThemeChanged("win11"), TransparencyChanged(40)) == [("#202020", 0.6)]


def test_classic_starts_opaque_in_its_own_colour():
    assert run(ThemeChanged("classic"), TransparencyChanged(0)) == [("#0c0f1d", 1.0)]


def test_percent_before_any_theme_is_ignored():
    assert run(TransparencyChanged(40)) == []


def test_same_tint_is_not_repeated():
    got = run(ThemeChanged("black"), TransparencyChanged(30), TransparencyChanged(30))
    assert got == [("#0E0E0E", 0.7)]


def test_switch_with_the_same_percent_changes_the_colour():
    got = run(
        ThemeChanged("classic"),
        TransparencyChanged(0),
        ThemeChanged("black"),
        TransparencyChanged(0),
    )
    assert got == [("#0c0f1d", 1.0), ("#0E0E0E", 1.0)]


def test_slider_changes_the_opacity():
    got = run(ThemeChanged("windows"), TransparencyChanged(0), TransparencyChanged(70))
    assert got == [("#202020", 1.0), ("#202020", 0.3)]


def test_other_events_are_ignored():
    assert run(StateChanged(State.IDLE)) == []


def test_no_theme_gives_a_zero_gradient_value():
    # GradientColor 0 makes Windows ignore the tint (the black theme did not change).
    for color in TINT_COLORS.values():
        assert make_tint(color, 0.0) != 0
