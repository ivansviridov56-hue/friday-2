"""Console chat to try the assistant's brain (and voice) by hand."""

from __future__ import annotations

import argparse
import logging

from friday.llm import AllProvidersFailed, LLMClient, trim_history
from friday.persona import build_system_prompt


def main(argv=None) -> None:
    from dotenv import load_dotenv

    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", action="store_true", help="speak the answers aloud")
    parser.add_argument("--debug", action="store_true", help="show timing logs")
    args = parser.parse_args(argv)

    load_dotenv()
    logging.basicConfig(level=logging.INFO if args.debug else logging.WARNING)
    speak = None
    if args.voice:
        from friday.audio import PygamePlayer
        from friday.tts import speak_text

        player = PygamePlayer()
        speak = lambda text: speak_text(text, player.play)

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
        if speak:
            speak(reply.text)


if __name__ == "__main__":
    main()
