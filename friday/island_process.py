"""Runs the Qt island as a child process and sends it the state (same interface as Island)."""

from __future__ import annotations

import logging
import math
import subprocess
import sys
import threading
import base64
from collections.abc import Callable
from typing import Any
from friday.eq_protocol import format_eq

log = logging.getLogger(__name__)

START_TIMEOUT = 15.0
STOP_TIMEOUT = 3.0


def _spawn() -> Any:
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    return subprocess.Popen(
        [sys.executable, "-m", "friday.island_quick"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        creationflags=flags,
    )


class IslandProcess:
    def __init__(self, spawn: Callable[[], Any] = _spawn) -> None:
        self._spawn = spawn
        self._proc: Any = None
        self._running = False
        self._ready_seen = False
        self._reader_done = threading.Event()
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> bool:
        """Start the island process. Returns False if it did not come up."""
        if self._running:
            return True
        try:
            proc = self._spawn()
        except OSError:
            log.exception("island: could not start the process")
            return False
        self._proc = proc
        self._ready_seen = False
        self._reader_done.clear()
        threading.Thread(
            target=self._read, args=(proc,), name="island-reader", daemon=True
        ).start()
        self._reader_done.wait(START_TIMEOUT)
        if not self._ready_seen or proc.poll() is not None:
            log.warning("island: the process did not report ready")
            self._kill(proc)
            self._proc = None
            return False
        self._running = True
        return True

    def set_state(self, state: str) -> None:
        """Show the colour of a state. Ignored when the island is not running."""
        self._send_word("state", state)

    def set_theme(self, theme: str) -> None:
        """Switch the colour theme. Ignored when the island is not running."""
        self._send_word("theme", theme)

    def set_accent(self, accent: str) -> None:
        """Send the Windows accent ('#rrggbb'). Ignored when the island is not running."""
        self._send_word("accent", accent)

    def set_look(self, look: str) -> None:
        """Switch the look of the icon (dot, eyes, equalizer). Ignored when not running."""
        self._send_word("look", look)

    def set_eq(self, levels: list[float]) -> None:
        """Send equalizer levels (0..1 per band). Ignored when not running."""
        if not levels:
            return
        self._send(f"eq {format_eq(levels)}\n")

    def show_text(self, text: str) -> None:
        """Show the answer text (sent as base64, never logged). Ignored when not running."""
        if not isinstance(text, str) or not text.strip():
            return
        payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
        self._send(f"text {payload}\n")

    def clear_text(self) -> None:
        """Hide the answer text. Ignored when not running."""
        self._send("clear\n")

    def start_reveal(self, text: str) -> None:
        """Show the answer text to be revealed in step with her voice (base64, never logged)."""
        if not isinstance(text, str) or not text.strip():
            return
        payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
        self._send(f"reveal {payload}\n")

    def reveal_chunk(self, start: int, end: int, seconds: float) -> None:
        """Tell the island that the piece text[start:end] starts to sound and lasts `seconds`."""
        if not isinstance(start, int) or not isinstance(end, int):
            return
        if start < 0 or end < start:
            return
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
            return
        if seconds < 0:
            return
        self._send(f"chunk {start} {end} {seconds:.3f}\n")

    def finish_reveal(self) -> None:
        """The speech is over: show the whole text at once. Ignored when not running."""
        self._send("done\n")

    def _send_word(self, command: str, value: str) -> None:
        if not isinstance(value, str) or not value or any(c.isspace() for c in value):
            return
        self._send(f"{command} {value}\n")

    def stop(self) -> None:
        """Close the island. Safe to call twice or without start()."""
        proc, self._proc = self._proc, None
        self._running = False
        if proc is None:
            return
        try:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
        except (OSError, ValueError):
            pass
        try:
            proc.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            proc.wait(STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            self._kill(proc)

    def _send(self, line: str) -> None:
        with self._lock:
            proc = self._proc
            if not self._running or proc is None:
                return
            try:
                proc.stdin.write(line)
                proc.stdin.flush()
            except (OSError, ValueError):
                log.warning("island: the process is gone")
                self._running = False

    def _read(self, proc: Any) -> None:
        """Reads the child's output; "ready" ends the wait in start(), EOF ends it too."""
        try:
            for line in proc.stdout:
                if line.strip() == "ready" and not self._ready_seen:
                    self._ready_seen = True
                    self._reader_done.set()
        except (OSError, ValueError):
            pass
        finally:
            self._reader_done.set()

    @staticmethod
    def _kill(proc: Any) -> None:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(2.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except OSError:
            log.debug("island: kill failed", exc_info=True)
