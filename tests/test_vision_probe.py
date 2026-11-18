import struct

import requests

from friday.vision_probe import (
    Provider,
    build_messages,
    probe_vision,
    run,
    solid_png,
)

PROVIDER = Provider("test", "https://example.test/v1", "some/model", "TEST_KEY")


class FakeResponse:
    def __init__(self, status: int = 200, body=None) -> None:
        self.status_code = status
        self._body = body

    def json(self):
        return self._body


def answer(text: str) -> dict:
    return {"choices": [{"message": {"content": text}}]}


def test_solid_png_has_png_signature_and_size() -> None:
    data = solid_png(size=16)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (16, 16)


def test_build_messages_has_text_and_image() -> None:
    messages = build_messages(b"abc")
    parts = messages[0]["content"]
    assert parts[0]["type"] == "text"
    assert parts[1]["type"] == "image_url"
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_probe_ok_when_color_is_named() -> None:
    post = lambda *a, **k: FakeResponse(200, answer("Красный."))
    result = probe_vision(PROVIDER, "key", post=post)
    assert result.status == "ok"


def test_probe_wrong_answer() -> None:
    post = lambda *a, **k: FakeResponse(200, answer("Синий."))
    assert probe_vision(PROVIDER, "key", post=post).status == "wrong_answer"


def test_probe_http_error_hides_the_key() -> None:
    body = {"error": {"message": "bad key SECRET"}}
    post = lambda *a, **k: FakeResponse(401, body)
    result = probe_vision(PROVIDER, "SECRET", post=post)
    assert result.status == "error"
    assert "HTTP 401" in result.detail
    assert "SECRET" not in result.detail


def test_probe_request_exception() -> None:
    def post(*args, **kwargs):
        raise requests.ConnectionError("down")

    result = probe_vision(PROVIDER, "key", post=post)
    assert result.status == "error"
    assert result.detail == "ConnectionError"


def test_probe_empty_answer() -> None:
    post = lambda *a, **k: FakeResponse(200, answer("  "))
    assert probe_vision(PROVIDER, "key", post=post).status == "empty_answer"


def test_run_without_keys() -> None:
    results = run(env={}, post=lambda *a, **k: FakeResponse())
    assert results
    assert all(r.status == "no_key" for r in results)


def test_run_puts_account_id_in_cloudflare_url() -> None:
    urls: list[str] = []

    def post(url, **kwargs):
        urls.append(url)
        return FakeResponse(200, answer("красный"))

    env = {
        "CLOUDFLARE_API_TOKEN": "t",
        "CLOUDFLARE_ACCOUNT_ID": "ACC123",
        "OPENROUTER_API_KEY": "o",
    }
    run(env=env, post=post)
    assert any("ACC123" in url for url in urls)
    assert not any("{account_id}" in url for url in urls)
