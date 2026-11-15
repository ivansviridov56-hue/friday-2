"""Console chat to try the assistant's brain by hand."""

from __future__ import annotations

import logging

from friday.llm import AllProvidersFailed, LLMClient, trim_history
from friday.persona import build_system_prompt


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.WARNING)
    client = LLMClient()
    history = [{"role": "system", "content": build_system_prompt()}]
    print("Пятница на связи. Пустая строка: выход.")
    while True:
        try:
            line = input("Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            break
        history.append({"role": "user", "content": line})
        try:
            reply = client.ask(history)
        except AllProvidersFailed as exc:
            print(f"[все провайдеры недоступны: {exc}]")
            history.pop()
            continue
        history.append({"role": "assistant", "content": reply.text})
        history = trim_history(history)
        print(f"Пятница [{reply.provider}, {reply.latency_ms} мс]: {reply.text}")


if __name__ == "__main__":
    main()
