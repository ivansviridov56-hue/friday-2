import base64

from friday.llm import LLMClient, Reply
from friday.screen_capture import Screenshot
from friday.vision import (
    DEFAULT_QUESTION,
    SYSTEM_PROMPT,
    VISION_CHAIN,
    VISION_MAX_TOKENS,
    VISION_TIMEOUT_S,
    build_messages,
    describe,
)

SHOT = Screenshot(
    data=b"\xff\xd8jpeg",
    mime="image/jpeg",
    width=1536,
    height=960,
    source_width=1920,
    source_height=1200,
)
ENV = {"CLOUDFLARE_ACCOUNT_ID": "ACC", "CLOUDFLARE_API_TOKEN": "cf-secret"}


class FakeClient:
    def __init__(self):
        self.calls = []

    def ask(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return Reply("На экране окно", "fake", 5)


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class Post:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append(kwargs)
        return self.outcomes.pop(0)


def test_messages_have_prompt_question_and_image():
    messages = build_messages(SHOT, "что тут?")
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    parts = messages[1]["content"]
    assert parts[0] == {"type": "text", "text": "что тут?"}
    encoded = base64.b64encode(SHOT.data).decode("ascii")
    assert parts[1]["image_url"]["url"] == f"data:image/jpeg;base64,{encoded}"


def test_empty_question_gets_default():
    messages = build_messages(SHOT, "   ")
    assert messages[1]["content"][0]["text"] == DEFAULT_QUESTION


def test_chain_order_without_gemma4_on_cloudflare():
    assert [e.name for e in VISION_CHAIN] == [
        "cf-mistral",
        "cf-llama4-scout",
        "or-gemma",
    ]


def test_describe_uses_vision_limits():
    client = FakeClient()
    reply = describe(client, SHOT, "что тут?")
    assert reply.text == "На экране окно"
    _, kwargs = client.calls[0]
    assert kwargs == {"timeout": VISION_TIMEOUT_S, "max_tokens": VISION_MAX_TOKENS}


def test_vision_chain_falls_back_with_long_timeout():
    ok = FakeResponse(200, {"choices": [{"message": {"content": "Окно"}}]})
    post = Post(FakeResponse(429), ok)
    client = LLMClient(chain=VISION_CHAIN, env=ENV, post=post)
    reply = describe(client, SHOT, "что тут?")
    assert reply.provider == "cf-llama4-scout"
    assert [c["timeout"] for c in post.calls] == [VISION_TIMEOUT_S] * 2
