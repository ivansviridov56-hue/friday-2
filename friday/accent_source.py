"""Reads the Windows accent palette from the registry. Live-checked, no unit tests."""

from __future__ import annotations

ACCENT_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"


class RegistryAccentSource:
    def palette(self) -> bytes | None:
        """Raw AccentPalette bytes, or None if the value is missing."""
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ACCENT_KEY) as key:
                value, kind = winreg.QueryValueEx(key, "AccentPalette")
        except OSError:
            return None
        return bytes(value) if kind == winreg.REG_BINARY else None
