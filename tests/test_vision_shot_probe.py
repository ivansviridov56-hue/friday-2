import pytest
import requests

from friday.probe import Provider
from friday.vision_shot_probe import ask, build_messages, fit_size, run

PROVIDER = Provider("test", "https://example.test/v1", "some/model", "TEST_KEY")


class FakeResponse:
    def __init__(self, status: int = 200, body=None) -> None:
        self.status_code = status
        self._body = body if body is not None else {}

    def json(self):
        return self._body


def answer(text: str) -> dict:
    return {"choices": [{"message": {"content": text}}]}


@pytest.mark.parametrize(
    ("size", "max_width", "expected"),
    [
        ((3000, 1500), 1500, (1500, 750)),
        ((800, 600), 1500, (800, 600)),
        ((3000, 1), 1000, (1000, 1)),
    ],
)
def test_fit_size(size, max_width, expected) -> None:
    assert fit_size(*size, max_width) == expected


def test_build_messages_has_prompt_and_data_url() -> None:
    parts = build_messages(b"abc", "image/jpeg", "что тут?")[0]["content"]
    assert parts[0] == {"type": "text", "text": "что тут?"}
    assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_ask_ok_returns_text() -> None:
    post = lambda *a, **k: FakeResponse(200, answer(" Окно браузера. "))
    result = ask(PROVIDER, "key", b"x", "image/jpeg", "?", post=post)
    assert result.status == "ok"
    assert result.text == "Окно браузера."
    assert result.latency_ms is not None


def test_ask_http_error_hides_the_key() -> None:
    body = {"error": {"message": "bad key SECRET"}}
    post = lambda *a, **k: FakeResponse(401, body)
    result = ask(PROVIDER, "SECRET", b"x", "image/jpeg", "?", post=post)
    assert result.status == "error"
    assert "HTTP 401" in result.text
    assert "SECRET" not in result.text


def test_ask_request_exception() -> None:
    def post(*args, **kwargs):
        raise requests.ConnectionError("down")

    result = ask(PROVIDER, "key", b"x", "image/jpeg", "?", post=post)
    assert result.status == "error"
    assert result.text == "ConnectionError"


def test_ask_empty_answer() -> None:
    post = lambda *a, **k: FakeResponse(200, answer("  "))
    result = ask(PROVIDER, "key", b"x", "image/jpeg", "?", post=post)
    assert result.status == "empty_answer"


def test_ask_bad_format() -> None:
    post = lambda *a, **k: FakeResponse(200, {})
    result = ask(PROVIDER, "key", b"x", "image/jpeg", "?", post=post)
    assert result.status == "error"
    assert result.text == "bad response format"


def test_run_without_keys() -> None:
    images = {"a": (b"x", "image/jpeg")}
    rows = run(images, env={}, post=lambda *a, **k: FakeResponse())
    assert rows
    assert all(row.answer.status == "no_key" for row in rows)


def test_run_uses_cloudflare_only_and_fills_account_id() -> None:
    urls: list[str] = []

    def post(url, **kwargs):
        urls.append(url)
        return FakeResponse(200, answer("ok"))

    images = {"a": (b"x", "image/jpeg"), "b": (b"y", "image/jpeg")}
    env = {
        "CLOUDFLARE_API_TOKEN": "t",
        "CLOUDFLARE_ACCOUNT_ID": "ACC123",
        "OPENROUTER_API_KEY": "o",
    }
    rows = run(images, env=env, post=post)
    assert len(rows) == len(urls) == 6  # 3 Cloudflare models x 2 images
    assert all("ACC123" in url for url in urls)
    assert not any("openrouter" in url for url in urls)
