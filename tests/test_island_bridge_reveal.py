from friday.island_bridge import MAX_REVEAL_CHARS, IslandBridge
from friday.ui_events import (
    MessageAdded,
    SpeechChunkStarted,
    State,
    StateChanged,
    UiEventBus,
)

TEXT = "Hello there. How are you doing today?"


class FakeIsland:
    def __init__(self) -> None:
        self.texts: list[str] = []
        self.clears = 0
        self.reveals: list[str] = []
        self.chunks: list[tuple[int, int, float]] = []
        self.finishes = 0

    def set_state(self, state: str) -> None:
        pass

    def set_theme(self, theme: str) -> None:
        pass

    def show_text(self, text: str) -> None:
        self.texts.append(text)

    def clear_text(self) -> None:
        self.clears += 1

    def start_reveal(self, text: str) -> None:
        self.reveals.append(text)

    def reveal_chunk(self, start: int, end: int, seconds: float) -> None:
        self.chunks.append((start, end, seconds))

    def finish_reveal(self) -> None:
        self.finishes += 1


class IdleTimer:
    def __init__(self, delay, callback) -> None:
        self.daemon = False

    def start(self) -> None:
        pass

    def cancel(self) -> None:
        pass


def make() -> tuple[UiEventBus, FakeIsland]:
    bus = UiEventBus()
    island = FakeIsland()
    IslandBridge(bus, island, timer_factory=IdleTimer).start()
    return bus, island


def test_spoken_answer_starts_a_reveal():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT))
    assert island.reveals == [TEXT]
    assert island.texts == []


def test_unspoken_answer_is_shown_at_once():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT, spoken=False))
    assert island.texts == [TEXT]
    assert island.reveals == []


def test_long_answer_is_shown_at_once():
    bus, island = make()
    bus.publish(MessageAdded("assistant", "word " * (MAX_REVEAL_CHARS // 5 + 10)))
    assert island.reveals == []
    assert len(island.texts) == 1


def test_chunks_are_located_in_order():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT))
    bus.publish(StateChanged(State.SPEAKING))
    bus.publish(SpeechChunkStarted("Hello there.", 1.0))
    bus.publish(SpeechChunkStarted("How are you doing today?", 2.0))
    assert island.chunks == [(0, 12, 1.0), (13, 37, 2.0)]


def test_repeated_piece_uses_the_next_occurrence():
    bus, island = make()
    bus.publish(MessageAdded("assistant", "Yes. Yes."))
    bus.publish(SpeechChunkStarted("Yes.", 1.0))
    bus.publish(SpeechChunkStarted("Yes.", 1.0))
    assert island.chunks == [(0, 4, 1.0), (5, 9, 1.0)]


def test_a_piece_outside_the_answer_is_ignored():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT))
    bus.publish(SpeechChunkStarted("Looking at the screen.", 1.0))
    bus.publish(SpeechChunkStarted("Hello there.", 1.0))
    assert island.chunks == [(0, 12, 1.0)]


def test_whitespace_is_collapsed_in_the_answer_and_in_pieces():
    bus, island = make()
    bus.publish(MessageAdded("assistant", "Hello there.   How are you?"))
    bus.publish(SpeechChunkStarted("How  are you?", 1.0))
    assert island.reveals == ["Hello there. How are you?"]
    assert island.chunks == [(13, 25, 1.0)]


def test_chunk_without_a_reveal_is_ignored():
    bus, island = make()
    bus.publish(SpeechChunkStarted("Hello there.", 1.0))
    assert island.chunks == []


def test_chunk_of_an_unspoken_answer_is_ignored():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT, spoken=False))
    bus.publish(SpeechChunkStarted("Hello there.", 1.0))
    assert island.chunks == []


def test_leaving_speaking_finishes_the_reveal():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT))
    bus.publish(StateChanged(State.SPEAKING))
    bus.publish(StateChanged(State.IDLE))
    assert island.finishes == 1
    bus.publish(SpeechChunkStarted("Hello there.", 1.0))
    assert island.chunks == []


def test_speaking_does_not_finish_the_reveal():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT))
    bus.publish(StateChanged(State.SPEAKING))
    assert island.finishes == 0


def test_idle_without_a_reveal_finishes_nothing():
    bus, island = make()
    bus.publish(StateChanged(State.IDLE))
    assert island.finishes == 0


def test_a_new_answer_resets_the_position():
    bus, island = make()
    bus.publish(MessageAdded("assistant", TEXT))
    bus.publish(SpeechChunkStarted("How are you doing today?", 2.0))
    bus.publish(MessageAdded("assistant", "Yes. Yes."))
    bus.publish(SpeechChunkStarted("Yes.", 1.0))
    assert island.chunks == [(13, 37, 2.0), (0, 4, 1.0)]
