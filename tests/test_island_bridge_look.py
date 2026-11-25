from friday.island_bridge import IslandBridge
from friday.ui_events import IslandLookChanged, UiEventBus


class FakeIsland:
    def __init__(self):
        self.looks = []

    def set_state(self, state):
        pass

    def set_theme(self, theme):
        pass

    def set_look(self, look):
        self.looks.append(look)

    def show_text(self, text):
        pass

    def clear_text(self):
        pass

    def start_reveal(self, text):
        pass

    def reveal_chunk(self, start, end, seconds):
        pass

    def finish_reveal(self):
        pass


def test_the_look_is_forwarded_to_the_island():
    bus = UiEventBus()
    island = FakeIsland()
    IslandBridge(bus, island).start()
    bus.publish(IslandLookChanged("eyes"))
    assert island.looks == ["eyes"]


def test_a_look_chosen_before_the_bridge_started_is_delivered():
    bus = UiEventBus()
    bus.publish(IslandLookChanged("equalizer"))
    island = FakeIsland()
    IslandBridge(bus, island).start()
    assert island.looks == ["equalizer"]


def test_nothing_is_forwarded_after_close():
    bus = UiEventBus()
    island = FakeIsland()
    bridge = IslandBridge(bus, island)
    bridge.start()
    bridge.close()
    bus.publish(IslandLookChanged("eyes"))
    assert island.looks == []
