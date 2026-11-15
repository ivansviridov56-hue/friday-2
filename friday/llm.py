"""Cloud LLM client with an ordered fallback chain."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)

CF_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

TIMEOUT_S = 15
COOLDOWN_S = 60.0
MAX_TOKENS = 300


@dataclass(frozen=True)
class Endpoint:
    name: str
    url: str
    model: str
    key_env: str


DEFAULT_CHAIN = [
    Endpoint(
        "cf-mistral",
        CF_URL,
        "@cf/mistralai/mistral-small-3.1-24b-instruct",
        "CLOUDFLARE_API_TOKEN",
    ),
    Endpoint(
        "cf-llama70b",
        CF_URL,
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "CLOUDFLARE_API_TOKEN",
    ),
    Endpoint(
        "or-gemma",
        OPENROUTER_URL,
        "google/gemma-4-26b-a4b-it:free",
        "OPENROUTER_API_KEY",
    ),
]


@dataclass(frozen=True)
class Reply:
    text: str
    provider: str
    latency_ms: int


class AllProvidersFailed(Exception):
    def __init__(self, reasons: dict[str, str]):
        self.reasons = reasons
        text = "; ".join(f"{name}: {why}" for name, why in reasons.items())
        super().__init__(text or "no providers configured")


def trim_history(messages: list[dict], keep: int = 20) -> list[dict]:
    """Keep all system messages and only the last `keep` other messages."""
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    return system + rest[-keep:]


class LLMClient:
    def __init__(self, chain=None, env=None, post=requests.post, clock=time.monotonic):
        self._chain = list(DEFAULT_CHAIN if chain is None else chain)
        self._env = os.environ if env is None else env
        self._post = post
        self._clock = clock
        self._blocked_until: dict[str, float] = {}

    def ask(self, messages: list[dict]) -> Reply:
        reasons: dict[str, str] = {}
        ready = []
        for endpoint in self._chain:
            problem = self._config_problem(endpoint)
            if problem:
                reasons[endpoint.name] = problem
            else:
                ready.append(endpoint)

        now = self._clock()
        active = [e for e in ready if self._blocked_until.get(e.name, 0.0) <= now]
        for endpoint in active or ready:
            outcome = self._try(endpoint, messages)
            if isinstance(outcome, Reply):
                return outcome
            reasons[endpoint.name] = outcome
            self._blocked_until[endpoint.name] = self._clock() + COOLDOWN_S
            log.warning("provider %s failed: %s", endpoint.name, outcome)
        raise AllProvidersFailed(reasons)

    def _config_problem(self, endpoint: Endpoint) -> str:
        if not self._env.get(endpoint.key_env, "").strip():
            return "key not set"
        if (
            "{account_id}" in endpoint.url
            and not self._env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
        ):
            return "account id not set"
        return ""

    def _try(self, endpoint: Endpoint, messages: list[dict]) -> Reply | str:
        url = endpoint.url.replace(
            "{account_id}", self._env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
        )
        key = self._env[endpoint.key_env].strip()
        started = self._clock()
        try:
            response = self._post(
                url,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": endpoint.model,
                    "messages": messages,
                    "max_tokens": MAX_TOKENS,
                },
                timeout=TIMEOUT_S,
            )
            if response.status_code != 200:
                return f"HTTP {response.status_code}"
            message = response.json()["choices"][0]["message"]
            text = (message.get("content") or "").strip()
        except requests.RequestException as exc:
            return type(exc).__name__
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            return "bad response format"
        if not text:
            return "empty answer"
        latency = int((self._clock() - started) * 1000)
        return Reply(text, endpoint.name, latency)
