"""Describe a screenshot with a cloud vision model (chain with fallback)."""

from __future__ import annotations

import base64
import logging

from typing import Protocol

from friday.llm import CF_URL, OPENROUTER_URL, Endpoint, LLMClient, Reply
from friday.screen_capture import Screenshot

log = logging.getLogger(__name__)

VISION_TIMEOUT_S = 30
VISION_MAX_TOKENS = 400
DEFAULT_QUESTION = "Что сейчас на экране?"

SYSTEM_PROMPT = (
    "You see a screenshot of the user's computer screen. Answer in Russian, "
    "in two or three short sentences of plain text, as if speaking aloud. "
    "No markdown, no lists, no formulas. Say only what is visible on the screen "
    "and do not guess what you cannot read."
)

VISION_CHAIN = [
    Endpoint(
        "cf-mistral",
        CF_URL,
        "@cf/mistralai/mistral-small-3.1-24b-instruct",
        "CLOUDFLARE_API_TOKEN",
    ),
    Endpoint(
        "cf-llama4-scout",
        CF_URL,
        "@cf/meta/llama-4-scout-17b-16e-instruct",
        "CLOUDFLARE_API_TOKEN",
    ),
    Endpoint(
        "or-gemma",
        OPENROUTER_URL,
        "google/gemma-4-26b-a4b-it:free",
        "OPENROUTER_API_KEY",
    ),
]


class Asker(Protocol):
    def ask(
        self,
        messages: list[dict],
        *,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> Reply: ...


def build_messages(screenshot: Screenshot, question: str) -> list[dict]:
    """Chat messages with the screenshot attached as a data URL."""
    text = question.strip() or DEFAULT_QUESTION
    encoded = base64.b64encode(screenshot.data).decode("ascii")
    url = f"data:{screenshot.mime};base64,{encoded}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": url}},
            ],
        },
    ]


def build_vision_client() -> LLMClient:
    """One client per assistant run, so provider cooldowns are remembered."""
    return LLMClient(chain=VISION_CHAIN)


def describe(client: Asker, screenshot: Screenshot, question: str) -> Reply:
    """Ask the vision chain about the screenshot; raises AllProvidersFailed."""
    return client.ask(
        build_messages(screenshot, question),
        timeout=VISION_TIMEOUT_S,
        max_tokens=VISION_MAX_TOKENS,
    )
