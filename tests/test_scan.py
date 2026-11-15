from friday.probe import ProbeResult
from friday.scan import free_models, rank, scan


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


MODELS = {"data": [{"id": "a/x:free"}, {"id": "b/y"}, {"id": "c/z:free"}]}


def fake_get(*args, **kwargs):
    return FakeResponse(MODELS)


def test_free_models_skips_paid():
    assert free_models(get=fake_get) == ["a/x:free", "c/z:free"]


def test_scan_probes_each_free_model():
    reply = {"choices": [{"message": {"content": "Минск"}}]}
    results = scan("k", post=lambda *a, **k: FakeResponse(reply), get=fake_get)
    assert [r.name for r in results] == ["a/x:free", "c/z:free"]
    assert all(r.status == "ok" for r in results)


def test_rank_puts_fast_working_models_first():
    results = [
        ProbeResult("slow", "ok", 900, ""),
        ProbeResult("broken", "error", 100, ""),
        ProbeResult("fast", "ok", 300, ""),
    ]
    assert [r.name for r in rank(results)] == ["fast", "slow", "broken"]
