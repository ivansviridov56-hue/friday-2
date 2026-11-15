"""Check which free LLM providers answer from this network, and how fast."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests

PROMPT = "Ответь одним словом: столица Беларуси?"
EXPECTED = "минск"
TIMEOUT_S = 20

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(frozen=True)
class Provider:
    name: str
    url: str
    model: str
    env_key: str


PROVIDERS = [
    Provider(
        "groq",
        "https://api.groq.com/openai/v1/chat/completions",
        "llama-3.3-70b-versatile",
        "GROQ_API_KEY",
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
    Provider(
        "or-nemotron",
        OPENROUTER_URL,
        "nvidia/nemotron-3.5-lightning:free",
        "OPENROUTER_API_KEY",
    ),
    Provider(
        "mistral",
        "https://api.mistral.ai/v1/chat/completions",
        "mistral-small-latest",
        "MISTRAL_API_KEY",
    ),
    Provider(
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "gemini-2.5-flash",
        "GEMINI_API_KEY",
    ),
]


@dataclass(frozen=True)
class ProbeResult:
    name: str
    status: str  # ok | wrong_answer | error | no_key
    latency_ms: int | None
    detail: str


def _error_text(response, api_key: str) -> str:
    """Short server error message, with the key removed."""
    try:
        data = response.json()
        error = data.get("error", data) if isinstance(data, dict) else data
        text = error.get("message", "") if isinstance(error, dict) else str(error)
    except Exception:
        return ""
    return str(text).replace(api_key, "***")[:80]


def probe(provider: Provider, api_key: str, post=requests.post) -> ProbeResult:
    """Send one tiny request. Never raises; never includes the key in output."""
    started = time.perf_counter()

    def elapsed_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        response = post(
            provider.url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": provider.model,
                "messages": [{"role": "user", "content": PROMPT}],
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


def run_all(env=os.environ, post=requests.post) -> list[ProbeResult]:
    results = []
    for provider in PROVIDERS:
        key = env.get(provider.env_key, "").strip()
        if not key:
            results.append(ProbeResult(provider.name, "no_key", None, "key not set"))
        else:
            results.append(probe(provider, key, post=post))
    return results


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    for r in run_all():
        latency = f"{r.latency_ms} ms" if r.latency_ms is not None else "-"
        print(f"{r.name:<12} {r.status:<13} {latency:<10} {r.detail}")


if __name__ == "__main__":
    main()
