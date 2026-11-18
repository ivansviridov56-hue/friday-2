import requests

from friday.llm import (
    MAX_TOKENS,
    TIMEOUT_S,
    AllProvidersFailed,
    LLMClient,
    trim_history,
)

ENV = {
    "CLOUDFLARE_ACCOUNT_ID": "ACC",
    "CLOUDFLARE_API_TOKEN": "cf-secret",
    "OPENROUTER_API_KEY": "or-secret",
}
MSGS = [{"role": "user", "content": "привет"}]


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def ok(text="Привет"):
    return FakeResponse(200, {"choices": [{"message": {"content": text}}]})


class Script:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.models = []
        self.calls = []

    def __call__(self, url, **kwargs):
        self.models.append(kwargs["json"]["model"])
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_first_provider_answers():
    client = LLMClient(env=ENV, post=Script(ok("Здравствуйте")))
    reply = client.ask(MSGS)
    assert reply.text == "Здравствуйте" and reply.provider == "cf-mistral"


def test_falls_back_on_rate_limit():
    script = Script(FakeResponse(429), ok())
    reply = LLMClient(env=ENV, post=script).ask(MSGS)
    assert reply.provider == "cf-llama70b" and len(script.models) == 2


def test_falls_back_on_timeout():
    script = Script(requests.ConnectTimeout(), ok())
    assert LLMClient(env=ENV, post=script).ask(MSGS).provider == "cf-llama70b"


def test_empty_answer_falls_through():
    script = Script(ok(""), ok("Есть"))
    assert LLMClient(env=ENV, post=script).ask(MSGS).text == "Есть"


def test_provider_without_key_is_skipped():
    env = {"OPENROUTER_API_KEY": "or-secret"}
    script = Script(ok())
    reply = LLMClient(env=env, post=script).ask(MSGS)
    assert reply.provider == "or-gemma" and len(script.models) == 1


def test_missing_account_id_skips_cloudflare():
    env = {"CLOUDFLARE_API_TOKEN": "cf-secret", "OPENROUTER_API_KEY": "or-secret"}
    reply = LLMClient(env=env, post=Script(ok())).ask(MSGS)
    assert reply.provider == "or-gemma"


def test_all_failed_raises_without_leaking_keys():
    script = Script(FakeResponse(500), FakeResponse(500), FakeResponse(401))
    try:
        LLMClient(env=ENV, post=script).ask(MSGS)
    except AllProvidersFailed as exc:
        text = str(exc)
        assert "HTTP 500" in text and "HTTP 401" in text
        assert "secret" not in text
    else:
        raise AssertionError("expected AllProvidersFailed")


def test_failed_provider_is_skipped_during_cooldown():
    now = [0.0]
    script = Script(FakeResponse(429), ok(), ok(), ok())
    client = LLMClient(env=ENV, post=script, clock=lambda: now[0])
    client.ask(MSGS)  # cf-mistral fails, cf-llama70b answers
    client.ask(MSGS)  # cf-mistral is cooling: goes straight to cf-llama70b
    assert len(script.models) == 3
    now[0] = 61.0
    client.ask(MSGS)  # cooldown over: cf-mistral is tried first again
    assert script.models[3] == script.models[0]


def test_everything_cooling_still_tries():
    now = [0.0]
    script = Script(FakeResponse(500), FakeResponse(500), FakeResponse(500), ok())
    client = LLMClient(env=ENV, post=script, clock=lambda: now[0])
    try:
        client.ask(MSGS)
    except AllProvidersFailed:
        pass
    assert client.ask(MSGS).provider == "cf-mistral"


def test_trim_history_keeps_system_and_latest():
    messages = [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": str(i)} for i in range(30)
    ]
    trimmed = trim_history(messages, keep=20)
    assert len(trimmed) == 21
    assert trimmed[0]["role"] == "system" and trimmed[-1]["content"] == "29"


def test_default_timeout_and_max_tokens():
    script = Script(ok())
    LLMClient(env=ENV, post=script).ask(MSGS)
    assert script.calls[0]["timeout"] == TIMEOUT_S
    assert script.calls[0]["json"]["max_tokens"] == MAX_TOKENS


def test_custom_timeout_and_max_tokens():
    script = Script(ok())
    LLMClient(env=ENV, post=script).ask(MSGS, timeout=30, max_tokens=400)
    assert script.calls[0]["timeout"] == 30
    assert script.calls[0]["json"]["max_tokens"] == 400


def test_custom_limits_apply_to_fallback_too():
    script = Script(FakeResponse(429), ok())
    LLMClient(env=ENV, post=script).ask(MSGS, timeout=30, max_tokens=400)
    assert [c["timeout"] for c in script.calls] == [30, 30]
    assert [c["json"]["max_tokens"] for c in script.calls] == [400, 400]
