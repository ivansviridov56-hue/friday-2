from friday.persona import build_system_prompt


def test_prompt_uses_given_address():
    assert "шеф" in build_system_prompt("шеф")


def test_prompt_defaults_to_boss():
    assert "босс" in build_system_prompt()


def test_prompt_requires_feminine_gender():
    assert "женском роде" in build_system_prompt()


def test_prompt_uses_informal_address():
    assert "на «ты»" in build_system_prompt()


def test_prompt_forbids_fake_abilities():
    assert "Не обещай умений" in build_system_prompt()
