"""List the models offered by GitHub Models and Cloudflare Workers AI."""

from __future__ import annotations

import os

import requests

GITHUB_CATALOG_URL = "https://models.github.ai/catalog/models"
CLOUDFLARE_SEARCH_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search"
)
TIMEOUT_S = 20


def github_models(token: str, get=requests.get) -> list[str]:
    response = get(
        GITHUB_CATALOG_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=TIMEOUT_S,
    )
    data = response.json()
    return [m["id"] for m in data if isinstance(m, dict) and "id" in m]


def cloudflare_text_models(account_id: str, token: str, get=requests.get) -> list[str]:
    response = get(
        CLOUDFLARE_SEARCH_URL.format(account_id=account_id),
        headers={"Authorization": f"Bearer {token}"},
        params={"task": "Text Generation"},
        timeout=TIMEOUT_S,
    )
    result = response.json().get("result", [])
    return [m["name"] for m in result if isinstance(m, dict) and "name" in m]


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    env = os.environ
    github = env.get("GITHUB_TOKEN", "").strip()
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    cloudflare = env.get("CLOUDFLARE_API_TOKEN", "").strip()

    for title, ready, fetch in [
        ("GitHub Models", bool(github), lambda: github_models(github)),
        (
            "Cloudflare Workers AI",
            bool(account and cloudflare),
            lambda: cloudflare_text_models(account, cloudflare),
        ),
    ]:
        print(f"\n== {title} ==")
        if not ready:
            print("keys not set in .env")
            continue
        try:
            for name in fetch():
                print(name)
        except (requests.RequestException, ValueError, AttributeError) as exc:
            print(f"failed: {type(exc).__name__}")


if __name__ == "__main__":
    main()
