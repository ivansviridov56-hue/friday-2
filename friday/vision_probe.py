"""Probe which free providers accept an image and answer about it.

Sends a tiny solid-red PNG and asks for its color. This checks that a provider
takes images through the OpenAI-style chat API and really looks at them; how
well a model reads small text on a real screenshot is a separate check.
"""

from __future__ import annotations

import base64
import os
import struct
import time
import zlib

import requests

from friday.cf_probe import CF_URL
from friday.probe import OPENROUTER_URL, ProbeResult, Provider, _error_text

PROMPT = "Какого цвета это изображение? Ответь одним словом."
EXPECTED = "красн"
TIMEOUT_S = 30

PROVIDERS = [
    Provider(
        "cf-mistral",
        CF_URL,
        "@cf/mistralai/mistral-small-3.1-24b-instruct",
        "CLOUDFLARE_API_TOKEN",
    ),
    Provider(
        "cf-llama4-scout",
        CF_URL,
        "@cf/meta/llama-4-scout-17b-16e-instruct",
        "CLOUDFLARE_API_TOKEN",
    ),
    Provider(
        "cf-gemma4",
        CF_URL,
        "@cf/google/gemma-4-26b-a4b-it",
        "CLOUDFLARE_API_TOKEN",
    ),
    Provider(
        "or-gemma26",
        OPENROUTER_URL,
        "google/gemma-4-26b-a4b-it:free",
        "OPENROUTER_API_KEY",
    ),
    Provider(
        "or-gemma31",
        OPENROUTER_URL,
        "google/gemma-4-31b-it:free",
        "OPENROUTER_API_KEY",
    ),
]


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def solid_png(rgb: tuple[int, int, int] = (255, 0, 0), size: int = 64) -> bytes:
    """A solid-color RGB PNG built with the standard library only."""
    row = b"\x00" + bytes(rgb) * size
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(row * size))
        + _chunk(b"IEND", b"")
    )


def build_messages(png: bytes) -> list[dict]:
    encoded = base64.b64encode(png).decode("ascii")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encoded}"},
                },
            ],
        }
    ]


def probe_vision(
    provider: Provider, api_key: str, post=requests.post, url: str | None = None
) -> ProbeResult:
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
                "messages": build_messages(solid_png()),
                "max_tokens": 150,
            },
            timeout=TIMEOUT_S,
        )
        if response.status_code != 200:
            extra = _error_text(response, api_key)
            detail = f"HTTP {response.status_code}" + (f": {extra}" if extra else "")
            return ProbeResult(provider.name, "error", elapsed_ms(), detail)
        message = response.json()["choices"][0]["message"]
        text = message.get("content") or ""
    except requests.RequestException as exc:
        return ProbeResult(provider.name, "error", None, type(exc).__name__)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return ProbeResult(provider.name, "error", elapsed_ms(), "bad response format")

    if not text.strip():
        return ProbeResult(provider.name, "empty_answer", elapsed_ms(), "empty content")
    status = "ok" if EXPECTED in text.lower() else "wrong_answer"
    return ProbeResult(provider.name, status, elapsed_ms(), text.strip()[:40])


def run(env=os.environ, post=requests.post) -> list[ProbeResult]:
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    results = []
    for provider in PROVIDERS:
        key = env.get(provider.env_key, "").strip()
        if not key:
            results.append(ProbeResult(provider.name, "no_key", None, "key not set"))
        elif "{account_id}" in provider.url and not account:
            results.append(
                ProbeResult(provider.name, "no_key", None, "account id not set")
            )
        else:
            url = provider.url.replace("{account_id}", account)
            results.append(probe_vision(provider, key, post=post, url=url))
    return results


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    for r in run():
        latency = f"{r.latency_ms} ms" if r.latency_ms is not None else "-"
        print(f"{r.name:<18} {r.status:<13} {latency:<9} {r.detail}")


if __name__ == "__main__":
    main()
