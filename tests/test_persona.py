from friday.persona import build_system_prompt


def test_prompt_uses_given_address():
    assert "шеф" in build_system_prompt("шеф")


def test_prompt_defaults_to_boss():
    assert "босс" in build_system_prompt()
