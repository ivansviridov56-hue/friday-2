"""Compare Russian answer quality and total time on a few Cloudflare models."""

from __future__ import annotations

import os
import time

import requests

from friday.cf_probe import CF_URL

MODELS = [
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/mistralai/mistral-small-3.1-24b-instruct",
    "@cf/meta/llama-4-scout-17b-16e-instruct",
]

SYSTEM = (
    "Ты голосовой ассистент. Отвечай по-русски, коротко и естественно, "
    "одной-тремя фразами, без списков и markdown."
)

PROMPTS = [
    "Привет! Как дела?",
    "Объясни простыми словами, что такое нейросеть.",
    "Придумай название для кота рыжего цвета.",
    "Мне скучно, предложи, чем заняться вечером.",
    "Сколько будет двадцать три умножить на семнадцать?",
]


def ask(
    url: str, token: str, model: str, prompt: str, post=requests.post
) -> tuple[str, int]:
    started = time.perf_counter()
    response = post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 200,
        },
        timeout=30,
    )
    elapsed = int((time.perf_counter() - started) * 1000)
    if response.status_code != 200:
        return f"[HTTP {response.status_code}]", elapsed
    try:
        text = response.json()["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError, ValueError):
        return "[bad response format]", elapsed
    return text.strip() or "[empty]", elapsed


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not (account and token):
        print("Cloudflare keys are not set in .env")
        return
    url = CF_URL.format(account_id=account)
    for model in MODELS:
        print(f"\n===== {model} =====")
        for prompt in PROMPTS:
            text, ms = ask(url, token, model, prompt)
            print(f"\n> {prompt}\n[{ms} ms] {text}")


if __name__ == "__main__":
    main()
