"""Probe every currently free OpenRouter model and rank the results."""

from __future__ import annotations

import os

import requests

from friday.probe import OPENROUTER_URL, ProbeResult, Provider, probe

MODELS_URL = "https://openrouter.ai/api/v1/models"


def free_models(get=requests.get) -> list[str]:
    data = get(MODELS_URL, timeout=20).json()["data"]
    return [m["id"] for m in data if m["id"].endswith(":free")]


def scan(api_key: str, post=requests.post, get=requests.get) -> list[ProbeResult]:
    results = []
    for model in free_models(get=get):
        provider = Provider(model, OPENROUTER_URL, model, "OPENROUTER_API_KEY")
        results.append(probe(provider, api_key, post=post))
    return results


def rank(results: list[ProbeResult]) -> list[ProbeResult]:
    """Working models first, fastest first."""
    return sorted(results, key=lambda r: (r.status != "ok", r.latency_ms or 10**9))


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        print("OPENROUTER_API_KEY is not set in .env")
        return
    for r in rank(scan(key)):
        latency = f"{r.latency_ms} ms" if r.latency_ms is not None else "-"
        print(f"{r.name:<50} {r.status:<13} {latency:<9} {r.detail}")


if __name__ == "__main__":
    main()
