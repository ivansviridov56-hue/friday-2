"""Probe a short list of Cloudflare Workers AI models."""

from __future__ import annotations

import os

import requests

from friday.probe import ProbeResult, Provider, probe

CF_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
)

MODELS = [
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/meta/llama-3.1-8b-instruct-fp8",
    "@cf/google/gemma-4-26b-a4b-it",
    "@cf/mistralai/mistral-small-3.1-24b-instruct",
    "@cf/meta/llama-4-scout-17b-16e-instruct",
]


def providers(account_id: str) -> list[Provider]:
    url = CF_URL.format(account_id=account_id)
    return [
        Provider(model.split("/", 1)[1], url, model, "CLOUDFLARE_API_TOKEN")
        for model in MODELS
    ]


def run(env=os.environ, post=requests.post) -> list[ProbeResult]:
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = env.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not (account and token):
        return [ProbeResult("cloudflare", "no_key", None, "keys not set")]
    return [probe(p, token, post=post) for p in providers(account)]


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    for r in run():
        latency = f"{r.latency_ms} ms" if r.latency_ms is not None else "-"
        print(f"{r.name:<45} {r.status:<13} {latency:<9} {r.detail}")


if __name__ == "__main__":
    main()
