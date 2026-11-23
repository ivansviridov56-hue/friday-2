from friday.window_lifecycle import WindowLifecycle


def make():
    calls: list[str] = []
    lifecycle = WindowLifecycle()
    lifecycle.bind(
        lambda: calls.append("show"),
        lambda: calls.append("hide"),
        lambda: calls.append("destroy"),
    )
    return lifecycle, calls


def test_unbound_lifecycle_does_nothing():
    lifecycle = WindowLifecycle()
    assert lifecycle.show() is False
    assert lifecycle.hide() is False
    assert lifecycle.quit() is False


def test_show_and_hide_call_the_bound_actions():
    lifecycle, calls = make()
    assert lifecycle.hide() is True
    assert lifecycle.show() is True
    assert calls == ["hide", "show"]


def test_closing_hides_instead_of_closing():
    lifecycle, calls = make()
    assert lifecycle.on_closing() is False  # False cancels the close
    assert calls == ["hide"]


def test_quit_destroys_and_then_closing_is_allowed():
    lifecycle, calls = make()
    assert lifecycle.quit() is True
    assert lifecycle.on_closing() is True
    assert calls == ["destroy"]


def test_closing_is_allowed_when_the_window_cannot_be_hidden():
    lifecycle = WindowLifecycle()
    assert lifecycle.on_closing() is True

    def broken():
        raise RuntimeError("boom")

    lifecycle.bind(lambda: None, broken, lambda: None)
    assert lifecycle.on_closing() is True


def test_broken_actions_do_not_raise():
    lifecycle = WindowLifecycle()

    def broken():
        raise RuntimeError("boom")

    lifecycle.bind(broken, broken, broken)
    assert lifecycle.show() is False
    assert lifecycle.hide() is False
    assert lifecycle.quit() is False


def test_failed_quit_does_not_leave_the_window_unhideable():
    lifecycle = WindowLifecycle()
    calls: list[str] = []

    def broken():
        raise RuntimeError("boom")

    lifecycle.bind(lambda: None, lambda: calls.append("hide"), broken)
    assert lifecycle.quit() is False
    assert lifecycle.on_closing() is False
    assert calls == ["hide"]


def test_unbind_stops_the_actions():
    lifecycle, calls = make()
    lifecycle.unbind()
    assert lifecycle.show() is False
    assert lifecycle.hide() is False
    assert lifecycle.quit() is False
    assert calls == []
