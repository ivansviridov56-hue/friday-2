"""Local fallback voice: Windows SAPI (System.Speech) through PowerShell.

Used when Edge TTS cannot voice a piece of text. The text reaches PowerShell as a base64
environment variable, never inside the command line, so quotes, `$(...)` or newlines in an
answer cannot break or hijack the command. Nothing about the text is written to disk;
only the finished WAV goes to a temp file that is deleted at once. Returns WAV bytes.
"""

from __future__ import annotations

import base64
import logging
import os
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

VOICE_NAME = "Microsoft Irina Desktop"
DEFAULT_RATE = 2  # SAPI scale from -10 to 10, 0 is normal speed
TIMEOUT_S = 20.0

_SCRIPT = """\
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($env:FRIDAY_TEXT_B64))
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice($env:FRIDAY_VOICE)
$speaker.Rate = [int]$env:FRIDAY_RATE
$speaker.SetOutputToWaveFile($env:FRIDAY_OUT)
$speaker.Speak($text)
$speaker.Dispose()
"""

Runner = Callable[..., Any]


class LocalTtsError(Exception):
    pass


def build_command() -> list[str]:
    encoded = base64.b64encode(_SCRIPT.encode("utf-16-le")).decode("ascii")
    return ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]


def build_env(
    text: str,
    out_path: str,
    voice: str,
    rate: int,
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    env.update(
        FRIDAY_TEXT_B64=base64.b64encode(text.encode("utf-8")).decode("ascii"),
        FRIDAY_VOICE=voice,
        FRIDAY_RATE=str(rate),
        FRIDAY_OUT=out_path,
    )
    return env


def synthesize_local(
    text: str,
    voice: str = VOICE_NAME,
    rate: int = DEFAULT_RATE,
    run: Runner = subprocess.run,
) -> bytes:
    """Voice `text` with the Windows voice and return WAV bytes."""
    if not text.strip():
        raise LocalTtsError("nothing to say")
    if not -10 <= rate <= 10:
        raise ValueError("rate must be between -10 and 10")
    handle, name = tempfile.mkstemp(suffix=".wav", prefix="friday_")
    os.close(handle)
    path = Path(name)
    started = time.perf_counter()
    try:
        try:
            result = run(
                build_command(),
                env=build_env(text, name, voice, rate),
                capture_output=True,
                timeout=TIMEOUT_S,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise LocalTtsError(type(exc).__name__) from exc
        if result.returncode != 0:
            detail = bytes(result.stderr or b"")[:200].decode("utf-8", "replace")
            raise LocalTtsError(f"powershell exit {result.returncode}: {detail}")
        data = path.read_bytes()
        if not data:
            raise LocalTtsError("the voice produced an empty file")
        log.info(
            "local voice: %d chars in %d ms",
            len(text),
            int((time.perf_counter() - started) * 1000),
        )
        return data
    finally:
        path.unlink(missing_ok=True)
