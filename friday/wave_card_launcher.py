"""Start a My Wave card chosen by a spoken title and confirm it.

Pure logic: everything that touches the Yandex Music window is injected, so it
is covered by tests. Chain: read the card names, pick the best one, press it
(a card that is out of view is pressed only to scroll the carousel, then it is
pressed again once it is visible), check that something plays.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol, TypeVar

from friday.wave_cards import cards_from_names, pick_card

logger = logging.getLogger(__name__)

T = TypeVar("T")

MAX_ROUNDS = 2


class CardStatus(Enum):
    STARTED = "started"
    NO_WINDOW = "no_window"
    NO_CARDS = "no_cards"
    NO_MATCH = "no_match"
    NOT_CONFIRMED = "not_confirmed"
    ERROR = "error"


@dataclass(frozen=True)
class CardResult:
    status: CardStatus
    title: str | None = None  # the card that was chosen, for the spoken answer


class WaveCardUi(Protocol):
    def card_names(self) -> list[str]: ...
    def card_visible(self, name: str) -> bool: ...
    def press_card(self, name: str) -> bool: ...


class WaveCardLauncher:
    def __init__(
        self,
        find_ui: Callable[[], WaveCardUi | None],
        is_playing: Callable[[], bool],
        *,
        prepare: Callable[[], None] | None = None,
        after_start: Callable[[], None] | None = None,
        window_timeout: float = 5.0,
        cards_timeout: float = 3.0,
        scroll_timeout: float = 3.0,
        confirm_timeout: float = 5.0,
        poll_interval: float = 0.3,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._find_ui = find_ui
        self._is_playing = is_playing
        self._prepare = prepare
        self._after_start = after_start
        self._window_timeout = window_timeout
        self._cards_timeout = cards_timeout
        self._scroll_timeout = scroll_timeout
        self._confirm_timeout = confirm_timeout
        self._interval = poll_interval
        self._sleep = sleep
        self._monotonic = monotonic

    def launch(self, query: str) -> CardResult:
        self._safe(self._prepare)
        try:
            return self._run(query)
        except Exception as error:
            logger.warning("wave card launch failed: %s", type(error).__name__)
            return CardResult(CardStatus.ERROR)
        finally:
            self._safe(self._after_start)

    def _run(self, query: str) -> CardResult:
        ui = self._poll(self._safe_find, self._window_timeout, lambda v: v is not None)
        if ui is None:
            logger.info("Yandex Music window not found")
            return CardResult(CardStatus.NO_WINDOW)
        names = self._poll(ui.card_names, self._cards_timeout, bool)
        if not names:
            logger.info("no wave cards on the page")
            return CardResult(CardStatus.NO_CARDS)
        card = pick_card(query, cards_from_names(names))
        if card is None:
            logger.info("no wave card matches the request")
            return CardResult(CardStatus.NO_MATCH)
        for _ in range(MAX_ROUNDS):
            was_visible = ui.card_visible(card.name)
            if not ui.press_card(card.name):
                logger.info("the card could not be pressed")
                return CardResult(CardStatus.ERROR, card.title)
            if was_visible:
                playing = self._poll(self._safe_playing, self._confirm_timeout, bool)
                status = CardStatus.STARTED if playing else CardStatus.NOT_CONFIRMED
                return CardResult(status, card.title)
            # a hidden copy only scrolls the carousel: wait, then press again
            shown = self._poll(
                lambda: ui.card_visible(card.name), self._scroll_timeout, bool
            )
            if not shown:
                return CardResult(CardStatus.NOT_CONFIRMED, card.title)
        return CardResult(CardStatus.NOT_CONFIRMED, card.title)

    def _safe(self, func: Callable[[], None] | None) -> None:
        if func is None:
            return
        try:
            func()
        except Exception as error:
            logger.debug("step failed: %s", type(error).__name__)

    def _safe_find(self) -> WaveCardUi | None:
        try:
            return self._find_ui()
        except Exception as error:
            logger.debug("window lookup failed: %s", type(error).__name__)
            return None

    def _safe_playing(self) -> bool:
        try:
            return bool(self._is_playing())
        except Exception as error:
            logger.debug("playback check failed: %s", type(error).__name__)
            return False

    def _poll(self, check: Callable[[], T], timeout: float, ok: Callable[[T], bool]):
        deadline = self._monotonic() + timeout
        while True:
            value = check()
            if ok(value):
                return value
            if self._monotonic() >= deadline:
                return None
            self._sleep(self._interval)
