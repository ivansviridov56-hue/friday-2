"""Generate TTS samples with several settings so they can be compared by ear."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

PHRASE = "Привет, босс. Все системы в норме. Чем могу помочь?"
OUT_DIR = Path("samples")
VOICE = "ru-RU-SvetlanaNeural"


@dataclass(frozen=True)
class Variant:
    name: str
    voice: str = VOICE
    rate: str = "+0%"
    pitch: str = "+0Hz"
    soft: bool = False  # drop commas to reduce pauses


VARIANTS = [
    Variant("svetlana-normal"),
    Variant("svetlana-r10", rate="+10%"),
    Variant("svetlana-r20", rate="+20%"),
    Variant("svetlana-r30", rate="+30%"),
    Variant("svetlana-r20-nocomma", rate="+20%", soft=True),
]


def soften_punctuation(text: str) -> str:
    """Drop commas (they add pauses); keep sentence-ending marks for intonation."""
    return text.replace(",", "").replace("  ", " ")


async def render_all(
    variants=VARIANTS, out_dir=OUT_DIR, phrase=PHRASE, communicate=None
) -> dict[str, str]:
    """Render every variant to an mp3. Returns name -> path or 'failed: <reason>'."""
    if communicate is None:
        import edge_tts

        communicate = edge_tts.Communicate
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}
    for variant in variants:
        path = out_dir / f"{variant.name}.mp3"
        text = soften_punctuation(phrase) if variant.soft else phrase
        try:
            speaker = communicate(
                text, variant.voice, rate=variant.rate, pitch=variant.pitch
            )
            await speaker.save(str(path))
            results[variant.name] = str(path)
        except Exception as exc:  # the service can fail in many ways
            path.unlink(missing_ok=True)
            results[variant.name] = f"failed: {type(exc).__name__}"
    return results


def main() -> None:
    for name, result in asyncio.run(render_all()).items():
        print(f"{name:<22} {result}")


if __name__ == "__main__":
    main()
