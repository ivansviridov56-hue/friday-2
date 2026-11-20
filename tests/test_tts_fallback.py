import base64
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from friday.tts_fallback import (
    LocalTtsError,
    build_command,
    build_env,
    synthesize_local,
)

NASTY = "Играет «Мои клиенты», 'quoted' \"double\" $(Remove-Item x) `n\nline2; & calc"


def make_run(wav: bytes = b"RIFFfake", code: int = 0, stderr: bytes = b""):
    calls: list[dict] = []

    def run(command, **kwargs):
        env = kwargs["env"]
        calls.append({"command": command, **kwargs})
        if code == 0 and wav:
            Path(env["FRIDAY_OUT"]).write_bytes(wav)
        return SimpleNamespace(returncode=code, stderr=stderr)

    run.calls = calls
    return run


def test_returns_the_wav_the_voice_wrote() -> None:
    run = make_run(b"RIFFdata")
    assert synthesize_local("Привет", run=run) == b"RIFFdata"


def test_text_travels_in_the_environment_not_in_the_command() -> None:
    run = make_run()
    synthesize_local(NASTY, run=run)
    call = run.calls[0]
    decoded = base64.b64decode(call["env"]["FRIDAY_TEXT_B64"]).decode("utf-8")
    assert decoded == NASTY
    assert all(
        "Remove-Item" not in part and "calc" not in part for part in call["command"]
    )


def test_command_is_fixed_and_encoded() -> None:
    command = build_command()
    assert command[:4] == [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
    ]
    assert command == build_command()


def test_voice_and_rate_are_passed_on() -> None:
    run = make_run()
    synthesize_local("Раз", voice="Microsoft Irina Desktop", rate=3, run=run)
    env = run.calls[0]["env"]
    assert env["FRIDAY_VOICE"] == "Microsoft Irina Desktop"
    assert env["FRIDAY_RATE"] == "3"


def test_run_has_a_timeout_and_captures_output() -> None:
    run = make_run()
    synthesize_local("Раз", run=run)
    assert run.calls[0]["timeout"] > 0
    assert run.calls[0]["capture_output"] is True


def test_temp_file_is_removed_after_success() -> None:
    run = make_run()
    synthesize_local("Раз", run=run)
    assert not Path(run.calls[0]["env"]["FRIDAY_OUT"]).exists()


def test_temp_file_is_removed_after_failure() -> None:
    run = make_run(code=1, stderr=b"boom")
    with pytest.raises(LocalTtsError, match="boom"):
        synthesize_local("Раз", run=run)
    assert not Path(run.calls[0]["env"]["FRIDAY_OUT"]).exists()


def test_empty_file_is_an_error() -> None:
    with pytest.raises(LocalTtsError):
        synthesize_local("Раз", run=make_run(wav=b""))


def test_timeout_becomes_a_local_error() -> None:
    def run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1)

    with pytest.raises(LocalTtsError):
        synthesize_local("Раз", run=run)


def test_missing_powershell_becomes_a_local_error() -> None:
    def run(command, **kwargs):
        raise FileNotFoundError("powershell")

    with pytest.raises(LocalTtsError):
        synthesize_local("Раз", run=run)


def test_blank_text_is_rejected_without_running() -> None:
    run = make_run()
    with pytest.raises(LocalTtsError):
        synthesize_local("   ", run=run)
    assert run.calls == []


def test_bad_rate_is_rejected() -> None:
    with pytest.raises(ValueError):
        synthesize_local("Раз", rate=11, run=make_run())


def test_build_env_keeps_other_variables() -> None:
    env = build_env("x", "out.wav", "V", 0, base={"PATH": "p"})
    assert env["PATH"] == "p" and env["FRIDAY_OUT"] == "out.wav"
