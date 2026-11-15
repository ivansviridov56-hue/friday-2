from friday.cf_probe import MODELS, providers, run


class FakeResponse:
    status_code = 200

    def json(self):
        return {"choices": [{"message": {"content": "Минск"}}]}


def test_providers_use_account_id_and_token_key():
    items = providers("ACC1")
    assert len(items) == len(MODELS)
    assert all("ACC1" in p.url for p in items)
    assert all(p.env_key == "CLOUDFLARE_API_TOKEN" for p in items)


def test_run_without_keys_makes_no_requests():
    results = run(env={}, post=lambda *a, **k: 1 / 0)
    assert [r.status for r in results] == ["no_key"]


def test_run_probes_every_model():
    env = {"CLOUDFLARE_ACCOUNT_ID": "ACC1", "CLOUDFLARE_API_TOKEN": "tok"}
    results = run(env=env, post=lambda *a, **k: FakeResponse())
    assert len(results) == len(MODELS)
    assert all(r.status == "ok" for r in results)
