from friday.bench import ask


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_ask_returns_text_and_time():
    payload = {"choices": [{"message": {"content": " Привет! "}}]}
    post = lambda *a, **k: FakeResponse(200, payload)
    text, ms = ask("u", "t", "m", "p", post=post)
    assert text == "Привет!" and ms >= 0


def test_ask_marks_http_error():
    post = lambda *a, **k: FakeResponse(429)
    assert ask("u", "t", "m", "p", post=post)[0] == "[HTTP 429]"


def test_ask_marks_empty_content():
    payload = {"choices": [{"message": {"content": None}}]}
    post = lambda *a, **k: FakeResponse(200, payload)
    assert ask("u", "t", "m", "p", post=post)[0] == "[empty]"
