"""Short-term conversation memory: the last few user/assistant exchanges."""

from __future__ import annotations

from collections import deque

Message = dict[str, str]


class ConversationHistory:
    def __init__(self, max_exchanges: int = 5) -> None:
        if max_exchanges < 1:
            raise ValueError("max_exchanges must be at least 1")
        self._exchanges: deque[tuple[str, str]] = deque(maxlen=max_exchanges)

    def __len__(self) -> int:
        return len(self._exchanges)

    def add_exchange(self, user_text: str, assistant_text: str) -> None:
        """Remember a finished exchange (call only after a successful reply)."""
        self._exchanges.append((user_text, assistant_text))

    def messages_with(self, user_text: str) -> list[Message]:
        """History plus the new user message, ready to send to the LLM."""
        messages: list[Message] = []
        for user, assistant in self._exchanges:
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": assistant})
        messages.append({"role": "user", "content": user_text})
        return messages

    def clear(self) -> None:
        self._exchanges.clear()
