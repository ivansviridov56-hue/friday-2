from friday.catalog import cloudflare_text_models, github_models


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_github_models_reads_ids():
    payload = [{"id": "a/b"}, {"name": "no id"}, {"id": "c/d"}]
    get = lambda *a, **k: FakeResponse(payload)
    assert github_models("t", get=get) == ["a/b", "c/d"]


def test_cloudflare_models_reads_names():
    payload = {"result": [{"name": "@cf/x/y"}, {"id": "skip"}, {"name": "@cf/z"}]}
    get = lambda *a, **k: FakeResponse(payload)
    assert cloudflare_text_models("acc", "t", get=get) == ["@cf/x/y", "@cf/z"]
