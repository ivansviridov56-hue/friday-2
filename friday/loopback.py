"""Captures what goes to the speakers (WASAPI loopback). Live-checked, no unit tests."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

BLOCK_FRAMES = 1024


class LoopbackCapture:
    """open() finds the loopback of the default speakers, start() streams blocks to a callback."""

    def __init__(self) -> None:
        self._pa: Any = None
        self._device: Any = None
        self._stream: Any = None
        self._failed = False
        self.rate = 0
        self.channels = 0

    def open(self) -> bool:
        """Find the device. False when there is none (the app goes on without the equalizer)."""
        if self._pa is not None:
            return True
        try:
            import pyaudiowpatch as pyaudio

            pa = pyaudio.PyAudio()
        except Exception:
            log.exception("loopback: PyAudio is not available")
            return False
        try:
            wasapi = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
            speakers = pa.get_device_info_by_index(wasapi["defaultOutputDevice"])
            device = speakers if speakers.get("isLoopbackDevice") else None
            if device is None:
                for loop in pa.get_loopback_device_info_generator():
                    if speakers["name"] in loop["name"]:
                        device = loop
                        break
            if device is None:
                log.warning("loopback: no loopback device for the default speakers")
                pa.terminate()
                return False
        except Exception:
            log.exception("loopback: could not find the device")
            pa.terminate()
            return False
        self._pa, self._device = pa, device
        self.rate = int(device["defaultSampleRate"])
        self.channels = int(device["maxInputChannels"])
        return True

    def start(self, on_block: Callable[[bytes], None]) -> bool:
        """Start streaming 16-bit blocks; on_block runs in the audio thread, keep it short."""
        if self._pa is None or self._stream is not None:
            return False
        import pyaudiowpatch as pyaudio

        self._failed = False

        def callback(in_data, frame_count, time_info, status):
            try:
                on_block(in_data)
            except Exception:
                if not self._failed:
                    self._failed = True
                    log.exception("loopback: the block handler failed")
            return None, pyaudio.paContinue

        try:
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                frames_per_buffer=BLOCK_FRAMES,
                input=True,
                input_device_index=self._device["index"],
                stream_callback=callback,
            )
        except Exception:
            log.exception("loopback: could not start the stream")
            return False
        return True

    def close(self) -> None:
        """Stop and release everything. Safe to call twice."""
        stream, self._stream = self._stream, None
        pa, self._pa = self._pa, None
        self._device = None
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                log.debug("loopback: closing the stream failed", exc_info=True)
        if pa is not None:
            try:
                pa.terminate()
            except Exception:
                log.debug("loopback: terminate failed", exc_info=True)
