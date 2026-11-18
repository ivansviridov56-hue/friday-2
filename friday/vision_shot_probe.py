"""Probe: how well do the free vision models describe a real screenshot?

Takes a screenshot, prepares a few sizes (JPEG) and asks each Cloudflare model
to describe the screen. Prints latency, request size and the answer, so the
quality can be judged by eye. Pillow is imported lazily (local requirements
only), so the pure logic stays testable in CI.

The screenshot is only held in memory and sent to Cloudflare: close private
windows before running.
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass

import requests

from friday.probe import Provider, _error_text
from friday.vision_probe import PROVIDERS

PROMPT = (
    "Опиши по-русски, что изображено на этом скриншоте: какое приложение или сайт, "
    "что на экране, и перепиши заметные заголовки и подписи. 3-5 предложений."
)
WIDTHS = (1024, 1536, 2048)
TIMEOUT_S = 40
MAX_TOKENS = 300
SHOW_CHARS = 400
START_DELAY_S = 5

CF_ENV_KEY = "CLOUDFLARE_API_TOKEN"


@dataclass(frozen=True)
class Answer:
    status: str  # ok | empty_answer | error | no_key
    latency_ms: int | None
    text: str


@dataclass(frozen=True)
class Row:
    model: str
    label: str
    size_kb: int
    answer: Answer


def fit_size(width: int, height: int, max_width: int) -> tuple[int, int]:
    """Scale down to max_width keeping the aspect ratio; never scale up."""
    if width <= max_width:
        return width, height
    return max_width, max(1, round(height * max_width / width))


def build_messages(image: bytes, mime: str, prompt: str) -> list[dict]:
    encoded = base64.b64encode(image).decode("ascii")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{encoded}"},
                },
            ],
        }
    ]


def ask(
    provider: Provider,
    api_key: str,
    image: bytes,
    mime: str,
    prompt: str,
    post=requests.post,
    url: str | None = None,
) -> Answer:
    """One request with an image. Never raises; never puts the key in the output."""
    started = time.perf_counter()

    def elapsed_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        response = post(
            url or provider.url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": provider.model,
                "messages": build_messages(image, mime, prompt),
                "max_tokens": MAX_TOKENS,
            },
            timeout=TIMEOUT_S,
        )
        if response.status_code != 200:
            extra = _error_text(response, api_key)
            detail = f"HTTP {response.status_code}" + (f": {extra}" if extra else "")
            return Answer("error", elapsed_ms(), detail)
        message = response.json()["choices"][0]["message"]
        text = (message.get("content") or "").strip()
    except requests.RequestException as exc:
        return Answer("error", None, type(exc).__name__)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return Answer("error", elapsed_ms(), "bad response format")
    if not text:
        return Answer("empty_answer", elapsed_ms(), "empty content")
    return Answer("ok", elapsed_ms(), text)


def run(
    images: dict[str, tuple[bytes, str]], env=os.environ, post=requests.post
) -> list[Row]:
    """Ask every Cloudflare vision model about every prepared image."""
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    key = env.get(CF_ENV_KEY, "").strip()
    rows = []
    for provider in (p for p in PROVIDERS if p.env_key == CF_ENV_KEY):
        for label, (data, mime) in images.items():
            size_kb = len(data) // 1024
            if not (key and account):
                answer = Answer("no_key", None, "keys not set")
            else:
                url = provider.url.replace("{account_id}", account)
                answer = ask(provider, key, data, mime, PROMPT, post=post, url=url)
            rows.append(Row(provider.name, label, size_kb, answer))
    return rows


def _grab():
    """Screenshot of the primary screen (Windows, real pixels, not scaled)."""
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    from PIL import ImageGrab

    return ImageGrab.grab()


def _variants(image) -> dict[str, tuple[bytes, str]]:
    from io import BytesIO

    from PIL import Image

    rgb = image.convert("RGB")
    result: dict[str, tuple[bytes, str]] = {}
    for max_width in WIDTHS:
        size = fit_size(rgb.width, rgb.height, max_width)
        small = rgb if size == rgb.size else rgb.resize(size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        small.save(buffer, "JPEG", quality=85)
        result[f"{size[0]}x{size[1]}"] = (buffer.getvalue(), "image/jpeg")
    return result


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    print(
        f"Через {START_DELAY_S} с снимаю экран. Открой безобидное окно с русским текстом."
    )
    time.sleep(START_DELAY_S)
    image = _grab()
    print(f"Снимок: {image.width}x{image.height}")
    for row in run(_variants(image)):
        latency = (
            f"{row.answer.latency_ms} ms" if row.answer.latency_ms is not None else "-"
        )
        print(
            f"\n== {row.model} | {row.label} | {row.size_kb} KB | {row.answer.status} | {latency}"
        )
        print(row.answer.text[:SHOW_CHARS])


if __name__ == "__main__":
    main()
