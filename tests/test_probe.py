import requests

from friday.probe import PROVIDERS, probe, run_all

PROVIDER = PROVIDERS[0]


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def answer(text):
    return {"choices": [{"message": {"content": text}}]}


def test_ok_answer():
    post = lambda *a, **k: FakeResponse(200, answer("Минск"))
    assert probe(PROVIDER, "k", post=post).status == "ok"


def test_wrong_answer():
    post = lambda *a, **k: FakeResponse(200, answer("Москва"))
    assert probe(PROVIDER, "k", post=post).status == "wrong_answer"


def test_http_error():
    post = lambda *a, **k: FakeResponse(403)
    result = probe(PROVIDER, "k", post=post)
    assert result.status == "error" and result.detail == "HTTP 403"


def test_network_error_does_not_raise():
    def post(*a, **k):
        raise requests.ConnectTimeout()

    result = probe(PROVIDER, "k", post=post)
    assert result.status == "error" and result.latency_ms is None


def test_bad_format():
    post = lambda *a, **k: FakeResponse(200, {"oops": 1})
    assert probe(PROVIDER, "k", post=post).detail == "bad response format"


def test_missing_key_is_skipped():
    results = run_all(env={}, post=lambda *a, **k: 1 / 0)
    assert {r.status for r in results} == {"no_key"}


def test_key_never_in_output():
    post = lambda *a, **k: FakeResponse(403)
    result = probe(PROVIDER, "SECRET123", post=post)
    assert "SECRET123" not in repr(result)


def test_error_message_is_shown_without_key():
    payload = {"error": {"message": "bad key SECRET123 rejected"}}
    post = lambda *a, **k: FakeResponse(401, payload)
    result = probe(PROVIDER, "SECRET123", post=post)
    assert "rejected" in result.detail
    assert "SECRET123" not in result.detail


def test_empty_content_does_not_crash():
    payload = {"choices": [{"message": {"content": None}}]}
    post = lambda *a, **k: FakeResponse(200, payload)
    assert probe(PROVIDER, "k", post=post).status == "empty_answer"
